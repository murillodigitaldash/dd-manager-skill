#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import shutil
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "skills", "dds", "scripts"))
sys.path.insert(0, os.path.join(RAIZ, "tests"))

import apoio          # noqa: E402
import contrato       # noqa: E402


class TestContrato(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_le_vault_e_gerador_do_frontmatter(self):
        apoio.projeto_fixture(self.tmp)
        c = contrato.ler(self.tmp)
        self.assertEqual(c["vault"], "vault")
        self.assertEqual(c["gerador"], ["python3", "ferramentas/gerador.py"])

    def test_zonas_vem_do_gerador(self):
        apoio.projeto_fixture(self.tmp)
        c = contrato.ler(self.tmp)
        self.assertEqual(c["zonas"]["reescrita"], ["10 Espelho"])
        self.assertEqual(c["zonas"]["semeada"], ["00 Mapas"])
        self.assertEqual(c["zonas"]["livre"], ["90 Notas"])
        self.assertEqual(c["origem_zonas"], "gerador")

    def test_fonte_e_prerequisitos_vem_do_gerador(self):
        apoio.projeto_fixture(self.tmp)
        c = contrato.ler(self.tmp)
        self.assertEqual(c["fonte"]["backlog"], "fonte/backlog.md")
        self.assertEqual(c["prerequisitos"], ["fonte/backlog.md"])

    def test_artefatos_tem_os_padroes_da_dds(self):
        apoio.projeto_fixture(self.tmp)
        c = contrato.ler(self.tmp)
        self.assertEqual(c["artefatos"]["diario"], "docs/superpowers/execucao")
        self.assertEqual(c["artefatos"]["planos"], "docs/superpowers/plans")
        self.assertEqual(c["artefatos"]["specs"], "docs/superpowers/specs")

    def test_frontmatter_sobrescreve_caminho_de_artefato(self):
        apoio.projeto_fixture(self.tmp)
        caminho = os.path.join(self.tmp, ".claude", "dd.md")
        with open(caminho, encoding="utf-8") as f:
            texto = f.read()
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(texto.replace("gerador: python3 ferramentas/gerador.py",
                                  "gerador: python3 ferramentas/gerador.py\n"
                                  "diario: registros/sessoes"))
        c = contrato.ler(self.tmp)
        self.assertEqual(c["artefatos"]["diario"], "registros/sessoes")

    def test_sem_contrato_falha_dizendo_o_caminho(self):
        apoio.projeto_fixture(self.tmp, com_contrato=False)
        with self.assertRaises(contrato.ContratoInvalido) as erro:
            contrato.ler(self.tmp)
        self.assertIn(".claude/dd.md", str(erro.exception))

    def test_frontmatter_sem_vault_falha_nomeando_a_chave(self):
        apoio.projeto_fixture(self.tmp)
        with open(os.path.join(self.tmp, ".claude", "dd.md"), "w",
                  encoding="utf-8") as f:
            f.write("---\ngerador: python3 ferramentas/gerador.py\n---\n")
        with self.assertRaises(contrato.ContratoInvalido) as erro:
            contrato.ler(self.tmp)
        self.assertIn("vault", str(erro.exception))

    def test_escape_quando_o_gerador_nao_responde_contrato(self):
        apoio.projeto_fixture(self.tmp)
        # Um gerador que ignora --contrato e sai com erro.
        with open(os.path.join(self.tmp, "ferramentas", "gerador.py"), "w",
                  encoding="utf-8") as f:
            f.write("import sys\nsys.exit(2)\n")
        escape = {"zonas": {"reescrita": ["A"], "semeada": ["B"], "livre": ["C"]},
                  "fonte": {"backlog": "x.md"},
                  "prerequisitos": ["x.md"]}
        with open(os.path.join(self.tmp, ".claude", "dd.contrato.json"), "w",
                  encoding="utf-8") as f:
            json.dump(escape, f)
        c = contrato.ler(self.tmp)
        self.assertEqual(c["zonas"]["reescrita"], ["A"])
        self.assertEqual(c["origem_zonas"], "escape")

    def test_sem_contrato_e_sem_escape_falha_nomeando_os_dois(self):
        apoio.projeto_fixture(self.tmp)
        with open(os.path.join(self.tmp, "ferramentas", "gerador.py"), "w",
                  encoding="utf-8") as f:
            f.write("import sys\nsys.exit(2)\n")
        with self.assertRaises(contrato.ContratoInvalido) as erro:
            contrato.ler(self.tmp)
        mensagem = str(erro.exception)
        self.assertIn("--contrato", mensagem)
        self.assertIn("dd.contrato.json", mensagem)

    def test_zona_faltando_no_json_do_gerador_falha(self):
        apoio.projeto_fixture(self.tmp)
        with open(os.path.join(self.tmp, "ferramentas", "gerador.py"), "w",
                  encoding="utf-8") as f:
            f.write('import json,sys\n'
                    'print(json.dumps({"zonas": {"reescrita": ["A"]}, '
                    '"fonte": {}, "prerequisitos": []}))\n')
        with self.assertRaises(contrato.ContratoInvalido) as erro:
            contrato.ler(self.tmp)
        self.assertIn("semeada", str(erro.exception))

    def test_gerador_respondendo_null_falha(self):
        apoio.projeto_fixture(self.tmp)
        # Gerador que imprime null válido mas sem estrutura.
        with open(os.path.join(self.tmp, "ferramentas", "gerador.py"), "w",
                  encoding="utf-8") as f:
            f.write("import json, sys\nprint(json.dumps(None))\n")
        with self.assertRaises(contrato.ContratoInvalido) as erro:
            contrato.ler(self.tmp)
        self.assertIn("objeto JSON", str(erro.exception))

    def test_zonas_no_frontmatter_sao_ignoradas_invariante(self):
        apoio.projeto_fixture(self.tmp)
        caminho = os.path.join(self.tmp, ".claude", "dd.md")
        with open(caminho, encoding="utf-8") as f:
            texto = f.read()
        # Tenta declarar zonas no frontmatter — devem ser ignoradas.
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(texto.replace("gerador: python3 ferramentas/gerador.py",
                                  "gerador: python3 ferramentas/gerador.py\n"
                                  "zonas: alguma-coisa\n"
                                  "prerequisitos: fake.md"))
        c = contrato.ler(self.tmp)
        # As zonas continuam vindo do gerador, não do frontmatter.
        self.assertEqual(c["zonas"]["reescrita"], ["10 Espelho"])
        self.assertEqual(c["zonas"]["semeada"], ["00 Mapas"])
        self.assertEqual(c["zonas"]["livre"], ["90 Notas"])
        self.assertEqual(c["origem_zonas"], "gerador")
        # Os pré-requisitos também vêm do gerador.
        self.assertEqual(c["prerequisitos"], ["fonte/backlog.md"])


if __name__ == "__main__":
    unittest.main()
