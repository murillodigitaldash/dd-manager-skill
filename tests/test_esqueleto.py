#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ESQUELETO = os.path.join(RAIZ, "skills", "dds", "scripts",
                         "esqueleto_gerador.py")


class TestEsqueleto(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        os.makedirs(os.path.join(self.tmp, "docs"))
        os.makedirs(os.path.join(self.tmp, "ferramentas"))
        self.gerador = os.path.join(self.tmp, "ferramentas", "gerar_cerebro.py")
        shutil.copy(ESQUELETO, self.gerador)
        self._escrever("docs/visao.md", "# Visão\n\nFala do [[backlog]].\n")
        self._escrever("docs/backlog.md", "# Backlog\n\n- item um\n")

    def _escrever(self, rel, texto):
        caminho = os.path.join(self.tmp, rel)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(texto)

    def _rodar(self, *args):
        return subprocess.run([sys.executable, self.gerador] + list(args),
                              cwd=self.tmp, capture_output=True, text=True,
                              check=False)

    def test_contrato_devolve_json_com_as_tres_zonas(self):
        r = self._rodar("--contrato")
        self.assertEqual(r.returncode, 0, r.stderr)
        c = json.loads(r.stdout)
        for zona in ("reescrita", "semeada", "livre"):
            self.assertIn(zona, c["zonas"])
        self.assertIn("prerequisitos", c)

    def test_gera_uma_nota_por_documento(self):
        r = self._rodar()
        self.assertEqual(r.returncode, 0, r.stderr)
        espelho = os.path.join(self.tmp, "cerebro", "10 Documentos")
        self.assertTrue(os.path.isfile(os.path.join(espelho, "visao.md")))
        self.assertTrue(os.path.isfile(os.path.join(espelho, "backlog.md")))

    def test_semeia_as_tres_zonas_na_primeira_geracao(self):
        self._rodar()
        for zona in ("00 Mapas", "70 Decisões em aberto", "90 Notas"):
            self.assertTrue(os.path.isdir(os.path.join(self.tmp, "cerebro", zona)),
                            zona)

    def test_regenerar_preserva_a_zona_semeada(self):
        self._rodar()
        alvo = os.path.join(self.tmp, "cerebro", "00 Mapas", "Índice.md")
        with open(alvo, "a", encoding="utf-8") as f:
            f.write("\nminha resposta\n")
        self._rodar()
        with open(alvo, encoding="utf-8") as f:
            self.assertIn("minha resposta", f.read())

    def test_regenerar_preserva_a_zona_livre(self):
        self._rodar()
        nota = os.path.join(self.tmp, "cerebro", "90 Notas", "ideia.md")
        with open(nota, "w", encoding="utf-8") as f:
            f.write("# ideia\n")
        self._rodar()
        self.assertTrue(os.path.isfile(nota))

    def test_regenerar_apaga_nota_orfa_da_zona_reescrita(self):
        self._rodar()
        os.remove(os.path.join(self.tmp, "docs", "backlog.md"))
        self._rodar()
        self.assertFalse(os.path.isfile(os.path.join(
            self.tmp, "cerebro", "10 Documentos", "backlog.md")))

    def test_semear_recusa_quando_a_zona_ja_existe(self):
        self._rodar()
        r = self._rodar("--semear")
        self.assertEqual(r.returncode, 1)
        self.assertIn("--semear", r.stdout + r.stderr)

    def test_verificar_acusa_link_quebrado_sem_escrever(self):
        self._rodar()
        # Verificar passa antes de remover backlog.md
        r = self._rodar("--verificar")
        self.assertEqual(r.returncode, 0, r.stderr)
        # Agora remove a nota alvo do link de visao.md
        os.remove(os.path.join(self.tmp, "docs", "backlog.md"))
        self._rodar()          # some a nota alvo do link de visao.md
        r = self._rodar("--verificar")
        self.assertEqual(r.returncode, 1)
        self.assertIn("backlog", r.stdout)

    def test_falta_de_prerequisito_para_antes_de_gerar(self):
        shutil.rmtree(os.path.join(self.tmp, "docs"))
        r = self._rodar()
        self.assertEqual(r.returncode, 1)
        self.assertIn("docs", r.stdout + r.stderr)
        self.assertFalse(os.path.isdir(os.path.join(self.tmp, "cerebro")))

    def test_preserva_estrutura_de_subpastas_evitando_colisoes(self):
        # Criar dois documentos com o mesmo nome em subpastas diferentes
        self._escrever("docs/adr/nota.md", "# Nota ADR\n\nDecisão 1\n")
        self._escrever("docs/rfcs/nota.md", "# Nota RFC\n\nDecisão 2\n")
        r = self._rodar()
        self.assertEqual(r.returncode, 0, r.stderr)
        espelho = os.path.join(self.tmp, "cerebro", "10 Documentos")
        # Ambas as notas devem existir em suas subpastas
        adr_nota = os.path.join(espelho, "adr", "nota.md")
        rfcs_nota = os.path.join(espelho, "rfcs", "nota.md")
        self.assertTrue(os.path.isfile(adr_nota))
        self.assertTrue(os.path.isfile(rfcs_nota))
        # Conteúdos devem ser distintos
        with open(adr_nota, encoding="utf-8") as f:
            adr_conteudo = f.read()
        with open(rfcs_nota, encoding="utf-8") as f:
            rfcs_conteudo = f.read()
        self.assertNotEqual(adr_conteudo, rfcs_conteudo)
        self.assertIn("Decisão 1", adr_conteudo)
        self.assertIn("Decisão 2", rfcs_conteudo)

    def test_verificar_examina_todas_notas_mesmo_com_nomes_iguais(self):
        # Duas notas de mesmo nome-base em subpastas diferentes
        # Uma vazia, outra com link quebrado — ambas devem ser reportadas
        self._escrever("docs/adr/analise.md", "")  # vazia
        self._escrever("docs/rfcs/analise.md", "# RFC\n\nVer [[inexistente]].\n")
        self._rodar()
        r = self._rodar("--verificar")
        self.assertEqual(r.returncode, 1)
        saida = r.stdout + r.stderr
        # Ambos os problemas devem ser reportados
        self.assertIn("nota vazia", saida)
        self.assertIn("link quebrado", saida)
        self.assertIn("inexistente", saida)

    def test_verificar_avisa_quando_nome_base_eh_ambiguo(self):
        # Duas notas com o mesmo nome-base em subpastas diferentes
        # Aviso (não erro) — retorna 0
        self._escrever("docs/adr/proposta.md", "# Proposta ADR\n")
        self._escrever("docs/rfcs/proposta.md", "# Proposta RFC\n")
        self._rodar()
        r = self._rodar("--verificar")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # Deve avisar que o nome é ambíguo com cabeçalho apropriado
        saida = r.stdout + r.stderr
        self.assertIn("aviso", saida)
        self.assertIn("nome ambíguo", saida)
        self.assertIn("proposta", saida)

    def test_verificar_link_para_nome_unico_funciona(self):
        # Link para um nome único deve funcionar mesmo com subpastas
        self._escrever("docs/adr/decisao.md", "# Decisão\n")
        self._escrever("docs/visao.md", "# Visão\n\nSeguindo [[decisao]].\n")
        self._rodar()
        r = self._rodar("--verificar")
        # Não deve reportar link quebrado
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_regenerar_apaga_nota_orfa_em_subpasta(self):
        # Nota órfã em subpasta deve ser apagada junto com subpasta
        self._escrever("docs/adr/rfc.md", "# RFC\n")
        self._rodar()
        # Verificar que a nota foi criada em subpasta
        adr_rfc = os.path.join(self.tmp, "cerebro", "10 Documentos", "adr", "rfc.md")
        self.assertTrue(os.path.isfile(adr_rfc))
        # Remover o documento-fonte
        os.remove(os.path.join(self.tmp, "docs", "adr", "rfc.md"))
        # Regenerar
        self._rodar()
        # Arquivo e subpasta devem ter sido apagados
        self.assertFalse(os.path.isfile(adr_rfc))
        adr_dir = os.path.join(self.tmp, "cerebro", "10 Documentos", "adr")
        self.assertFalse(os.path.isdir(adr_dir))

    def test_verificar_link_ambiguo_retorna_zero(self):
        # Link apontando para nome-base duplicado é aviso, não erro
        # Deve aparecer como "link ambíguo", nomear os candidatos, retornar 0
        self._escrever("docs/adr/config.md", "# Config ADR\n")
        self._escrever("docs/rfcs/config.md", "# Config RFC\n")
        self._escrever("docs/visao.md", "# Visão\n\nVer [[config]].\n")
        self._rodar()
        r = self._rodar("--verificar")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        saida = r.stdout + r.stderr
        # Deve avisar sobre link ambíguo, não quebrado
        self.assertIn("link ambíguo", saida)
        self.assertIn("config", saida)
        self.assertNotIn("link quebrado", saida)

    def test_verificar_so_ambiguidade_sem_erros_retorna_zero(self):
        # Apenas ambiguidade (nomes duplicados), sem link quebrado e sem nota vazia
        # Retorna 0
        self._escrever("docs/adr/proposta.md", "# Proposta ADR\n")
        self._escrever("docs/rfcs/proposta.md", "# Proposta RFC\n")
        self._rodar()
        r = self._rodar("--verificar")
        self.assertEqual(r.returncode, 0)
        saida = r.stdout + r.stderr
        # Deve ter aviso, mas não erro
        self.assertIn("aviso", saida)
        self.assertNotIn("erro", saida)

    def test_verificar_link_genuinamente_inexistente_retorna_um(self):
        # Link para nome que não existe em lugar nenhum é erro
        self._escrever("docs/visao.md", "# Visão\n\nVer [[inexistente]].\n")
        self._rodar()
        r = self._rodar("--verificar")
        self.assertEqual(r.returncode, 1)
        saida = r.stdout + r.stderr
        self.assertIn("erro", saida)
        self.assertIn("link quebrado", saida)
        self.assertIn("inexistente", saida)

    def test_verificar_nota_vazia_com_ambiguidade_retorna_um(self):
        # Nota vazia (erro) junto com ambiguidade (aviso)
        # Retorna 1 e mostra ambos com cabeçalhos diferentes
        self._escrever("docs/adr/config.md", "# Config ADR\n")
        self._escrever("docs/rfcs/config.md", "# Config RFC\n")
        self._escrever("docs/visao.md", "")  # vazia
        self._rodar()
        r = self._rodar("--verificar")
        self.assertEqual(r.returncode, 1)
        saida = r.stdout + r.stderr
        # Deve mostrar erro (nota vazia) e aviso (ambiguidade) com cabeçalhos diferentes
        self.assertIn("erro", saida)
        self.assertIn("aviso", saida)
        self.assertIn("nota vazia", saida)
        self.assertIn("nome ambíguo", saida)


if __name__ == "__main__":
    unittest.main()
