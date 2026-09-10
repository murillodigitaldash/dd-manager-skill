#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
O plugin não pode citar caminho de projeto específico.

Este teste existe porque a primeira versão da DD cobrava um documento e uma
pasta do projeto onde nasceu, pelo nome, e por isso não rodava em nenhum
projeto além daquele. O defeito tinha duas formas, e as duas são mecânicas —
então a verificação também é, e é feita pela FORMA do defeito, não pelo nome
de um projeto específico (o repositório é público; nomear o projeto aqui
reintroduziria o mesmo problema dentro do próprio teste que o proíbe):

1. Um caminho absoluto de sistema de arquivos (`/Users/...`, `/home/...`,
   `C:\\...`) só faz sentido na máquina de quem o escreveu.
2. Um comando que invoca um script da própria plugin por um caminho relativo
   a um projeto (em vez de `$CLAUDE_PLUGIN_ROOT`) só funciona no projeto onde
   esse caminho relativo existe.

`docs/` e `tests/` ficam de fora: a spec e as fixtures podem legitimamente
citar exemplos concretos para argumentar e para testar. O que viaja para a
máquina de quem instala o plugin é só `skills/`, `commands/` e
`.claude-plugin/`, e é isso que este teste varre.
"""

import os
import re
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# As pastas que viajam para a máquina de quem instala o plugin.
PASTAS_DO_PLUGIN = ["skills", "commands", ".claude-plugin"]

PASTA_COMANDOS = os.path.join(RAIZ, "commands")

# A FORMA de um caminho absoluto de sistema de arquivos — Unix ou Windows —,
# não o nome de projeto nenhum. `\b` antes da letra de unidade evita casar
# dentro de uma palavra comum (ex.: o "o:" de "Formato:\n" numa docstring);
# `\S` no fim exige pelo menos mais um caractere depois do prefixo.
CAMINHO_ABSOLUTO = re.compile(r"(?:/Users/|/home/|\b[A-Za-z]:\\)\S")


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

    def test_todo_comando_invoca_script_da_plugin_so_via_claude_plugin_root(self):
        # Um comando que cita o arquivo de um script da própria plugin sem
        # passar por $CLAUDE_PLUGIN_ROOT voltou a depender de onde esse
        # script mora num projeto em particular.
        nomes_de_script = scripts_da_plugin()
        achados = []
        for nome_arquivo in sorted(os.listdir(PASTA_COMANDOS)):
            if not nome_arquivo.endswith(".md"):
                continue
            with open(os.path.join(PASTA_COMANDOS, nome_arquivo),
                      encoding="utf-8") as f:
                linhas = f.read().split("\n")
            for n, linha in enumerate(linhas, start=1):
                for nome_script in nomes_de_script:
                    if nome_script in linha and "CLAUDE_PLUGIN_ROOT" not in linha:
                        achados.append(
                            "%s:%d cita %s sem $CLAUDE_PLUGIN_ROOT → %s" % (
                                nome_arquivo, n, nome_script, linha.strip()))
        self.assertEqual(achados, [], "\n".join([""] + achados))

    def test_o_plugin_tem_arquivos_para_varrer(self):
        # Sem isto, os dois testes acima passariam por vacuidade num repo
        # vazio ou numa plugin sem nenhum script.
        self.assertGreater(len(list(arquivos_do_plugin())), 0,
                           "nenhum arquivo de plugin encontrado — "
                           "os testes acima passariam sem verificar nada")
        self.assertGreater(len(scripts_da_plugin()), 0,
                           "nenhum script encontrado em skills/ — o teste de "
                           "invocação passaria sem verificar nada")


if __name__ == "__main__":
    unittest.main()
