#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Forma da skill e dos comandos. O comportamento se prova rodando."""

import os
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(RAIZ, "skills", "dds", "SKILL.md")
COMANDOS = os.path.join(RAIZ, "commands")

ESPERADOS = ["Start.md", "Status.md", "Next.md", "Save.md", "End.md", "Build.md"]


def frontmatter(caminho):
    with open(caminho, encoding="utf-8") as f:
        linhas = f.read().split("\n")
    if not linhas or linhas[0].strip() != "---":
        return None
    campos = {}
    for linha in linhas[1:]:
        if linha.strip() == "---":
            return campos
        if ":" in linha:
            chave, valor = linha.split(":", 1)
            campos[chave.strip()] = valor.strip()
    return None


class TestSkill(unittest.TestCase):

    def test_a_skill_existe_e_se_chama_dds(self):
        self.assertTrue(os.path.isfile(SKILL), SKILL)
        campos = frontmatter(SKILL)
        self.assertIsNotNone(campos, "SKILL.md sem frontmatter fechado")
        self.assertEqual(campos.get("name"), "dds")

    def test_a_descricao_diz_quando_usar(self):
        campos = frontmatter(SKILL)
        self.assertTrue(campos.get("description"))
        self.assertLessEqual(len(campos["description"]), 1024)


class TestComandos(unittest.TestCase):

    def test_os_seis_comandos_existem(self):
        presentes = sorted(n for n in os.listdir(COMANDOS) if n.endswith(".md"))
        self.assertEqual(presentes, sorted(ESPERADOS))

    def test_todo_comando_tem_description(self):
        for nome in ESPERADOS:
            campos = frontmatter(os.path.join(COMANDOS, nome))
            self.assertIsNotNone(campos, "%s sem frontmatter" % nome)
            self.assertTrue(campos.get("description"), "%s sem description" % nome)

    def test_todo_comando_resolve_o_contrato(self):
        # Um comando que não resolve o contrato voltou a assumir caminho fixo.
        for nome in ESPERADOS:
            with open(os.path.join(COMANDOS, nome), encoding="utf-8") as f:
                texto = f.read()
            self.assertIn("contrato.py", texto,
                          "%s não resolve o contrato" % nome)
            self.assertIn("CLAUDE_PLUGIN_ROOT", texto,
                          "%s não chama o script pelo caminho do plugin" % nome)


if __name__ == "__main__":
    unittest.main()
