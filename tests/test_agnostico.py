#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
O plugin não pode citar caminho de projeto específico.

Este teste existe porque a primeira versão da DD cobrava
`proposta_sistema_governanca_incorporacoes.md` pelo nome, e por isso não rodava
em nenhum projeto além daquele em que nasceu. O defeito é mecânico, então a
verificação também é.

`docs/` e `tests/` ficam de fora: a spec e as fixtures precisam citar o caso
real para argumentar e para testar.
"""

import os
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# As pastas que viajam para a máquina de quem instala o plugin.
PASTAS_DO_PLUGIN = ["skills", "commands", ".claude-plugin"]

# Termos que só existem no projeto onde a DD nasceu. Se um deles aparecer no
# plugin, o plugin voltou a ser de um projeto só.
PROIBIDOS = [
    "cota-incorporacao",
    "g2m",
    "proposta_sistema_governanca",
    "16-backlog-priorizado",
    "15-adrs",
    "05-matriz-alcadas",
    "ferramentas/atualizar_cerebro",
]


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


class TestAgnostico(unittest.TestCase):

    def test_nenhum_arquivo_do_plugin_cita_projeto_especifico(self):
        achados = []
        for caminho in arquivos_do_plugin():
            with open(caminho, encoding="utf-8") as f:
                texto = f.read().lower()
            for termo in PROIBIDOS:
                if termo.lower() in texto:
                    achados.append("%s → %s" % (
                        os.path.relpath(caminho, RAIZ), termo))
        self.assertEqual(achados, [], "\n".join([""] + achados))

    def test_o_plugin_tem_arquivos_para_varrer(self):
        # Sem isto, o teste acima passaria por vacuidade num repo vazio.
        self.assertGreater(len(list(arquivos_do_plugin())), 0,
                           "nenhum arquivo de plugin encontrado — "
                           "o teste acima passaria sem verificar nada")


if __name__ == "__main__":
    unittest.main()
