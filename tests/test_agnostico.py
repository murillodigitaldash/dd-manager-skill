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
   existe no projeto que o tem. A defesa aqui é uma allowlist de duas
   metades: os nomes concretos são DERIVADOS das constantes `ARQUIVO_*` dos
   scripts do plugin — quem escreve o arquivo o declara, e a allowlist segue
   sozinha —, e só as formas de artefato (`AAAA-MM-DD-...`, globs) ficam à
   mão, porque não têm código de onde derivar. Um nome de documento
   específico de projeto não casa com nenhuma das duas metades, e reprova —
   sem o teste precisar saber nome de projeto nenhum.

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
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Os scripts do plugin são importados como módulos — não rodados — para ler
# deles os nomes de arquivo que eles declaram escrever. Nenhum dos três faz
# nada ao ser importado: todos guardam o trabalho atrás de `__main__`.
sys.path.insert(0, os.path.join(RAIZ, "skills", "dds", "scripts"))
import contrato          # noqa: E402
import esqueleto_gerador  # noqa: E402
import semeador          # noqa: E402

# As pastas que viajam para a máquina de quem instala o plugin.
PASTAS_DO_PLUGIN = ["skills", "commands", ".claude-plugin"]

# A FORMA de um caminho absoluto de sistema de arquivos — Unix, home do
# usuário ou Windows —, não o nome de projeto nenhum. `\b` antes da letra de
# unidade evita casar dentro de uma palavra comum (ex.: o "o:" de
# "Formato:\n" numa docstring); `\S` no fim exige pelo menos mais um
# caractere depois do prefixo, para não pegar o prefixo sozinho.
CAMINHO_ABSOLUTO = re.compile(
    r"(?:/Users/|/home/|/opt/|/var/|/Volumes/|/mnt/|~/|\b[A-Za-z]:\\)\S")

# A allowlist de `.md` tem duas metades, e só uma delas cresce quando a
# plugin cresce. Misturar as duas era o defeito: dez formas escritas à mão,
# e nada que lembrasse de estender a lista quando um arquivo novo nascesse —
# então o teste passava a reprovar trabalho legítimo, e o conserto dependia
# de alguém lembrar.
#
# METADE (a), derivada: nome concreto de arquivo existe porque algum código
# do plugin o escreve. Esses vêm das constantes `ARQUIVO_*` dos módulos
# abaixo, e não são repetidos aqui. Declarar o arquivo onde ele é escrito
# basta; a allowlist segue sozinha. É o mesmo padrão que `scripts_da_plugin()`
# já usa para os `.py`: derivar do que existe, não de lista à mão.
MODULOS_DO_PLUGIN = (contrato, esqueleto_gerador, semeador)

# METADE (b), à mão: forma de nome, não arquivo. Não há código de onde
# derivá-las — são os padrões dos artefatos que o projeto produz, e a DDS os
# reconhece sem nunca os escrever. Quase não mudam, e por isso o custo de
# mantê-las aqui é baixo — mas nome concreto de arquivo não entra
# (`test_a_metade_manual_da_allowlist_e_so_forma_de_artefato` reprova).
PADROES_DE_ARTEFATO = frozenset([
    "AAAA-MM-DD-sessao.md",
    "AAAA-MM-DD-*.md",
    "*-sessao.md",
    "AAAA-MM-DD-<fase>-<plano>-ledger.md",
    "*.md",
])


def nomes_md_declarados():
    """Nomes `.md` que o próprio código do plugin declara escrever.

    Lidos das constantes `ARQUIVO_*` dos módulos do plugin — não de uma lista
    mantida à mão aqui. Um arquivo novo declarado assim no script que o
    escreve entra na allowlist sem que ninguém precise lembrar deste teste.
    """
    nomes = set()
    for modulo in MODULOS_DO_PLUGIN:
        for atributo, valor in vars(modulo).items():
            if (atributo.startswith("ARQUIVO_")
                    and isinstance(valor, str) and valor.endswith(".md")):
                nomes.add(valor)
    return nomes


def allowlist_md():
    return nomes_md_declarados() | set(PADROES_DE_ARTEFATO)


def explicacao_da_allowlist(achados):
    """A mensagem de falha. Acusar não basta: ela precisa dizer o conserto.

    São dois lugares legítimos, e qual é qual depende do que o nome é — não
    de qual dá menos trabalho.
    """
    return "\n".join([""] + achados + [
        "",
        "Um `.md` citado pelo nome que não casa com forma nenhuma da DDS é,",
        "por eliminação, documento de um projeto específico — e citá-lo aqui",
        "é o defeito que esta regra existe para pegar.",
        "",
        "Se o arquivo é da própria DDS, há dois lugares onde declará-lo:",
        "",
        "  - é arquivo que algum script do plugin escreve → declare-o como",
        "    constante `ARQUIVO_*` nesse script. A allowlist o lê de lá.",
        "  - é forma de artefato do projeto (data, glob, placeholder), que a",
        "    DDS reconhece mas nunca escreve → acrescente a forma a",
        "    `PADROES_DE_ARTEFATO`, neste arquivo.",
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
    permitidos = allowlist_md()
    achados = []
    for m in LITERAL_MD.finditer(texto):
        token = m.group(0)
        base = token.rsplit("/", 1)[-1]
        if base not in permitidos:
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
        self.assertEqual(achados, [], explicacao_da_allowlist(achados))

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

    def test_nome_declarado_por_script_entra_na_allowlist_sozinho(self):
        # A regressão que este teste existe para pegar não é um nome de
        # projeto vazando — é o contrário: a plugin ganha um arquivo próprio,
        # ninguém lembra de estender a allowlist à mão, e o teste passa a
        # reprovar trabalho legítimo. A allowlist deriva das constantes
        # `ARQUIVO_*` dos scripts, então declarar o arquivo onde ele é
        # escrito basta — não há segunda lista para lembrar.
        semeador.ARQUIVO_INVENTADO_PELO_TESTE = "coisa-nova.md"
        try:
            self.assertIn("coisa-nova.md", nomes_md_declarados())
        finally:
            del semeador.ARQUIVO_INVENTADO_PELO_TESTE

    def test_os_nomes_da_allowlist_vem_dos_scripts_que_os_escrevem(self):
        # Cada nome concreto de arquivo da allowlist tem que ser declarado
        # pelo código que o escreve — não repetido aqui. Se um deles sumir
        # daqui é porque sumiu de lá, e aí a allowlist tem que encolher
        # junto.
        self.assertEqual(
            nomes_md_declarados(),
            {"dd.md", "backlog.md", "indice.md", "Índice.md",
             "visao-geral.md"})

    def test_a_metade_manual_da_allowlist_e_so_forma_de_artefato(self):
        # A metade que sobrou à mão não pode ganhar nome concreto de arquivo
        # de volta: nome concreto tem código que o escreve, e é de lá que ele
        # deve vir. O que mora aqui é forma — data, glob ou placeholder —,
        # que não tem código de onde derivar.
        for padrao in PADROES_DE_ARTEFATO:
            self.assertTrue(
                "*" in padrao or "AAAA-MM-DD" in padrao,
                "%r é nome concreto de arquivo, não forma de artefato — "
                "declare-o como constante ARQUIVO_* no script que o "
                "escreve" % padrao)

    def test_a_falha_da_allowlist_ensina_onde_declarar_o_nome(self):
        # Sem isto a mensagem só acusa. Quem topa com ela precisa saber que
        # há dois lugares legítimos, e qual é qual — senão o conserto vira
        # adivinhação, ou pior, acrescentar à mão o que deveria ser derivado.
        mensagem = explicacao_da_allowlist(["proposta_do_projeto.md"])
        self.assertIn("ARQUIVO_", mensagem)
        self.assertIn("PADROES_DE_ARTEFATO", mensagem)

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
