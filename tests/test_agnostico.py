#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
O plugin não pode citar caminho de projeto específico.

Este teste existe porque a primeira versão da DD cobrava um documento e uma
pasta do projeto onde nasceu, pelo nome, e por isso não rodava em nenhum
projeto além daquele. O defeito tinha três formas possíveis, e as três são
mecânicas — então a verificação também é, e é feita pela FORMA do defeito,
não pelo nome de um projeto específico (o repositório é público; nomear o
projeto aqui reintroduziria o mesmo problema dentro do próprio teste que o
proíbe):

1. Um caminho absoluto de sistema de arquivos (`/Users/...`, `/home/...`,
   `~/...`, `/opt/...`, `/var/...`, `/Volumes/...`, `/mnt/...`, `C:\\...`) só
   faz sentido na máquina de quem o escreveu.
2. Um comando que invoca um script da própria plugin por um caminho relativo
   a um projeto (em vez de `$CLAUDE_PLUGIN_ROOT`) só funciona no projeto onde
   esse caminho relativo existe.
3. Um documento citado pelo nome — `algum-documento-do-projeto.md` — só
   existe no projeto que o tem. A defesa aqui é uma allowlist: todo literal
   terminado em `.md` dentro de um arquivo do plugin precisa casar com uma
   forma que a própria DDS usa (`dd.md`, `Índice.md`, os padrões de artefato
   `AAAA-MM-DD-...`). Um nome de documento específico de projeto não casa
   com nenhuma forma da lista, e reprova — sem o teste precisar saber nome
   de projeto nenhum.

Uma rodada de revisão anterior comparou a primeira versão deste arquivo (uma
lista de sete termos proibidos por nome) contra as regras 1 e 2 acima e
achou que elas não pegavam a FORMA como o defeito histórico de fato
ocorreu — um documento de projeto citado por caminho relativo, em prosa. A
regra 3 fecha esse buraco;
`test_regras_estruturais_pegam_a_forma_historica_do_defeito`, mais abaixo,
prova isso rodando os sete termos originais — guardados só aqui, em tests/,
que, como docs/, pode legitimamente citar o caso real para testar.

`docs/` e `tests/` ficam de fora do que é varrido: a spec e as fixtures
podem citar exemplos concretos para argumentar e para testar. O que viaja
para a máquina de quem instala o plugin é só `skills/`, `commands/` e
`.claude-plugin/`, e é isso que este teste varre.
"""

import os
import re
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# As pastas que viajam para a máquina de quem instala o plugin.
PASTAS_DO_PLUGIN = ["skills", "commands", ".claude-plugin"]

# A FORMA de um caminho absoluto de sistema de arquivos — Unix, home do
# usuário ou Windows —, não o nome de projeto nenhum. `\b` antes da letra de
# unidade evita casar dentro de uma palavra comum (ex.: o "o:" de
# "Formato:\n" numa docstring); `\S` no fim exige pelo menos mais um
# caractere depois do prefixo, para não pegar o prefixo sozinho.
CAMINHO_ABSOLUTO = re.compile(
    r"(?:/Users/|/home/|/opt/|/var/|/Volumes/|/mnt/|~/|\b[A-Za-z]:\\)\S")

# Formas de nome de arquivo `.md` que a própria DDS usa hoje, levantadas
# varrendo skills/ e commands/. Qualquer outro literal `.md` num arquivo do
# plugin é, por eliminação, específico de um projeto — não desta plugin.
# `visao-geral.md` é o nome fixo do documento de semeadura que /dds:Build
# escreve quando entrevista um projeto sem documentação nenhuma (ver
# commands/Build.md, passo 2): é convenção da própria DDS, não de um
# projeto — por isso entra na lista, e não é exceção a ela.
ALLOWLIST_MD = frozenset([
    "dd.md",
    "AAAA-MM-DD-sessao.md",
    "AAAA-MM-DD-*.md",
    "*-sessao.md",
    "AAAA-MM-DD-<fase>-<plano>-ledger.md",
    "*.md",
    "Índice.md",
    "visao-geral.md",
])

# Um literal `.md`: uma sequência de caracteres de nome/caminho terminada em
# ".md", não seguida de mais um caractere de palavra (para não confundir
# ".mdx" com ".md"). Inclui `<`, `>` e `*` porque a própria DDS usa esses
# caracteres em placeholders e globs na prosa (ex.:
# `AAAA-MM-DD-<fase>-<plano>-ledger.md`).
LITERAL_MD = re.compile(r"[\w./*<>-]+\.md(?!\w)", re.UNICODE)


def arquivos_do_plugin():
    for pasta in PASTAS_DO_PLUGIN:
        base = os.path.join(RAIZ, pasta)
        if not os.path.isdir(base):
            continue
        for dirpath, _, nomes in os.walk(base):
            for nome in nomes:
                if nome.startswith("."):
                    continue
                yield os.path.join(dirpath, nome)


def arquivos_md_do_plugin():
    for caminho in arquivos_do_plugin():
        if caminho.endswith(".md"):
            yield caminho


def scripts_da_plugin():
    """Nomes-base (com extensão) dos scripts que a plugin traz em skills/.

    Derivado dos arquivos que realmente existem — não de uma lista escrita à
    mão — para que a checagem valha para qualquer script que a plugin vier a
    ganhar, sem precisar ser lembrada de novo.
    """
    base = os.path.join(RAIZ, "skills")
    nomes = set()
    for _, _, arquivos in os.walk(base):
        for nome in arquivos:
            if nome.endswith(".py"):
                nomes.add(nome)
    return nomes


def scripts_sem_claude_plugin_root(linha, nomes_de_script):
    """Nomes de script referenciados por CAMINHO em `linha`, sem
    `$CLAUDE_PLUGIN_ROOT` nela.

    Só conta como referência a menção que é de fato um caminho — o nome do
    script precedido de "/", como em ".../scripts/contrato.py" — ou uma
    invocação explícita (`python3 contrato.py`). Uma prosa que só nomeia o
    script para explicá-lo (\"as guardas de `guarda.py` leem...\") não é um
    caminho relativo a projeto nenhum, e não é o defeito que esta regra
    existe para pegar.
    """
    if "CLAUDE_PLUGIN_ROOT" in linha:
        return []
    achados = []
    for nome in nomes_de_script:
        if ("/" + nome) in linha or re.search(
                r"python3\s+[\"']?\S*" + re.escape(nome), linha):
            achados.append(nome)
    return achados


def literais_md_fora_da_allowlist(texto):
    """Literais `.md` em `texto` cujo nome-base não está na allowlist."""
    achados = []
    for m in LITERAL_MD.finditer(texto):
        token = m.group(0)
        base = token.rsplit("/", 1)[-1]
        if base not in ALLOWLIST_MD:
            achados.append(token)
    return achados


class TestAgnostico(unittest.TestCase):

    def test_nenhum_caminho_absoluto_de_sistema_de_arquivos(self):
        achados = []
        for caminho in arquivos_do_plugin():
            with open(caminho, encoding="utf-8") as f:
                linhas = f.read().split("\n")
            for n, linha in enumerate(linhas, start=1):
                if CAMINHO_ABSOLUTO.search(linha):
                    achados.append("%s:%d → %s" % (
                        os.path.relpath(caminho, RAIZ), n, linha.strip()))
        self.assertEqual(achados, [], "\n".join([""] + achados))

    def test_todo_md_do_plugin_invoca_script_so_via_claude_plugin_root(self):
        # Um `.md` que cita o arquivo de um script da própria plugin sem
        # passar por $CLAUDE_PLUGIN_ROOT voltou a depender de onde esse
        # script mora num projeto em particular. Varre skills/, commands/ e
        # .claude-plugin/ inteiros — não só commands/ — porque a SKILL.md
        # também invoca os scripts, e antes não era conferida.
        nomes_de_script = scripts_da_plugin()
        achados = []
        for caminho in arquivos_md_do_plugin():
            with open(caminho, encoding="utf-8") as f:
                linhas = f.read().split("\n")
            for n, linha in enumerate(linhas, start=1):
                for nome_script in scripts_sem_claude_plugin_root(
                        linha, nomes_de_script):
                    achados.append(
                        "%s:%d cita %s sem $CLAUDE_PLUGIN_ROOT → %s" % (
                            os.path.relpath(caminho, RAIZ), n, nome_script,
                            linha.strip()))
        self.assertEqual(achados, [], "\n".join([""] + achados))

    def test_todo_literal_md_casa_com_forma_da_propria_plugin(self):
        # Um `.md` citado pelo nome que não é nem um arquivo próprio da DDS
        # (`dd.md`, `Índice.md`) nem um dos padrões de artefato dela
        # (`AAAA-MM-DD-...`) é, por eliminação, nome de documento de um
        # projeto específico — a mesma forma do defeito histórico.
        achados = []
        for caminho in arquivos_do_plugin():
            with open(caminho, encoding="utf-8") as f:
                texto = f.read()
            for token in literais_md_fora_da_allowlist(texto):
                achados.append("%s → %s" % (
                    os.path.relpath(caminho, RAIZ), token))
        self.assertEqual(achados, [], "\n".join([""] + achados))

    def test_o_plugin_tem_arquivos_para_varrer(self):
        # Sem isto, os testes acima passariam por vacuidade num repo vazio,
        # numa plugin sem nenhum script ou sem nenhum comando em Markdown.
        self.assertGreater(len(list(arquivos_do_plugin())), 0,
                           "nenhum arquivo de plugin encontrado — "
                           "os testes acima passariam sem verificar nada")
        self.assertGreater(len(scripts_da_plugin()), 0,
                           "nenhum script encontrado em skills/ — o teste de "
                           "invocação passaria sem verificar nada")
        self.assertGreater(len(list(arquivos_md_do_plugin())), 0,
                           "nenhum .md encontrado em skills/, commands/ ou "
                           ".claude-plugin/ — os testes de invocação e de "
                           "allowlist passariam sem verificar nada")

    def test_regras_estruturais_pegam_a_forma_historica_do_defeito(self):
        # Regressão de um achado de revisão: a primeira versão deste
        # arquivo listava sete termos proibidos por nome; as regras
        # estruturais que os substituíram precisam continuar pegando os
        # mesmos sete, na forma em que o defeito de fato ocorreu — um
        # caminho de projeto citado dentro de prosa, não a palavra solta.
        # (Uma regra que só reagisse à palavra solta pegaria qualquer texto
        # que a mencionasse, o que não é o defeito - é falar sobre ele.)
        # Os termos moram só aqui, em tests/, que pode citar o caso real
        # para testar — ver docstring do módulo.
        termos_historicos = [
            "cota-incorporacao",
            "g2m",
            "proposta_sistema_governanca",
            "16-backlog-priorizado",
            "15-adrs",
            "05-matriz-alcadas",
            "ferramentas/atualizar_cerebro",
        ]
        nomes_de_script = scripts_da_plugin()
        for termo in termos_historicos:
            linha = "Leia `docs/%s.md` antes de gerar." % termo
            pega_absoluto = bool(CAMINHO_ABSOLUTO.search(linha))
            pega_script = bool(
                scripts_sem_claude_plugin_root(linha, nomes_de_script))
            pega_md = bool(literais_md_fora_da_allowlist(linha))
            self.assertTrue(
                pega_absoluto or pega_script or pega_md,
                "termo histórico não pego por nenhuma regra estrutural: "
                "%r (absoluto=%s script=%s md=%s)" % (
                    termo, pega_absoluto, pega_script, pega_md))


if __name__ == "__main__":
    unittest.main()
