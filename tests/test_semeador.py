#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A semeadura da fonte é do plugin, e é código — não prosa.

Antes deste script, `commands/Build.md` instruía o agente a criar
`visao-geral.md`, `backlog.md` e `adrs/indice.md` dentro da pasta-fonte, com
três saídas: cria o que falta, preserva o que existe, avisa quando falta a
estrutura que o protocolo lê. Instrução em prosa não tem teste, e o que não
tem teste não tem trava: nada impedia uma execução de sobrescrever o
`backlog.md` que o usuário trouxe de um histórico próprio — na primeira vez
que ele roda a plugin.

O que estes testes prendem, então, é a regra de escrita, não o conteúdo: o
corpo de `visao-geral.md` continua vindo do agente (é feito das respostas da
entrevista), mas quem decide escrever, preservar ou avisar é o script.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEMEADOR = os.path.join(RAIZ, "skills", "dds", "scripts", "semeador.py")


class TestSemeador(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        os.makedirs(os.path.join(self.tmp, "docs"))

    def _escrever(self, rel, texto):
        caminho = os.path.join(self.tmp, rel)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(texto)

    def _ler(self, rel):
        with open(os.path.join(self.tmp, rel), encoding="utf-8") as f:
            return f.read()

    def _rodar(self, *args, **kwargs):
        return subprocess.run([sys.executable, SEMEADOR] + list(args),
                              cwd=self.tmp, capture_output=True, text=True,
                              check=False, input=kwargs.get("entrada"))

    def _vereditos(self, saida):
        """Mapa caminho → veredito, do JSON que o script imprime."""
        return {a["caminho"]: a["veredito"]
                for a in json.loads(saida)["arquivos"]}

    def test_cria_backlog_e_indice_de_adrs_quando_faltam(self):
        r = self._rodar("--fonte", "docs")
        self.assertEqual(r.returncode, 0, r.stderr)
        vereditos = self._vereditos(r.stdout)
        self.assertEqual(vereditos[os.path.join("docs", "backlog.md")],
                         "criado")
        self.assertEqual(
            vereditos[os.path.join("docs", "adrs", "indice.md")], "criado")
        # A estrutura que o protocolo lê tem que estar lá — não basta o
        # arquivo existir. `### Execução` é de onde sai a fila de execução;
        # `Contador:` é de onde sai a numeração da próxima decisão.
        self.assertIn("### Execução", self._ler("docs/backlog.md"))
        self.assertIn("Contador:", self._ler("docs/adrs/indice.md"))

    def test_preserva_byte_a_byte_o_arquivo_que_ja_existe(self):
        # A razão de o script existir. Um `backlog.md` de histórico próprio,
        # com a estrutura que o protocolo lê, tem que sair da semeadura
        # idêntico ao que entrou — não "equivalente", idêntico.
        meu = ("# Backlog do meu jeito\n\nItens que eu já tinha.\n\n"
               "### Execução\n\n- item que eu escrevi\n")
        self._escrever("docs/backlog.md", meu)
        r = self._rodar("--fonte", "docs")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self._ler("docs/backlog.md"), meu)
        self.assertEqual(self._vereditos(r.stdout)[
            os.path.join("docs", "backlog.md")], "preservado")

    def test_avisa_estrutura_faltando_sem_consertar_sozinho(self):
        # Um backlog sem `### Execução` é ilegível para a fila de execução.
        # O script não conserta: consertar seria reescrever o arquivo do
        # usuário, que é a coisa que ele existe para não fazer. Avisa, nomeia
        # o que falta, e a decisão é de quem escreveu.
        meu = "# Backlog\n\nSó um texto solto, sem a seção que o protocolo lê.\n"
        self._escrever("docs/backlog.md", meu)
        r = self._rodar("--fonte", "docs")
        self.assertEqual(self._ler("docs/backlog.md"), meu)
        vereditos = self._vereditos(r.stdout)
        self.assertEqual(vereditos[os.path.join("docs", "backlog.md")],
                         "estrutura_incompleta")
        falta = [a["falta"] for a in json.loads(r.stdout)["arquivos"]
                 if a["caminho"] == os.path.join("docs", "backlog.md")][0]
        self.assertIn("### Execução", " ".join(falta))

    def test_visao_geral_recebe_o_corpo_pelo_stdin(self):
        # O corpo vem do agente porque é feito das respostas da entrevista —
        # o script não inventa conteúdo no lugar do usuário. O que é do
        # script é a regra de escrita, não o texto.
        corpo = "# Meu projeto\n\n## Do que se trata\n\nDe uma coisa.\n"
        r = self._rodar("--fonte", "docs", "--visao-geral", "-",
                        entrada=corpo)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self._ler("docs/visao-geral.md"), corpo)
        self.assertEqual(self._vereditos(r.stdout)[
            os.path.join("docs", "visao-geral.md")], "criado")

    def test_visao_geral_existente_nao_e_sobrescrita_pelo_stdin(self):
        # O caso que mais custa: o usuário escreveu a visão-geral à mão entre
        # uma pergunta e outra da entrevista, e a resposta do agente chega
        # depois. A dele fica.
        dele = "# O que eu escrevi\n\nMinhas palavras.\n"
        self._escrever("docs/visao-geral.md", dele)
        r = self._rodar("--fonte", "docs", "--visao-geral", "-",
                        entrada="# O que o agente montou\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self._ler("docs/visao-geral.md"), dele)
        self.assertEqual(self._vereditos(r.stdout)[
            os.path.join("docs", "visao-geral.md")], "preservado")

    def test_sem_a_flag_o_json_traz_so_os_dois_estruturais(self):
        # Sem `--visao-geral`, o script não tem corpo para escrever e não
        # inventa um: o JSON fala de dois arquivos, e `visao-geral.md` não
        # nasce.
        r = self._rodar("--fonte", "docs")
        self.assertEqual(len(json.loads(r.stdout)["arquivos"]), 2)
        self.assertFalse(
            os.path.exists(os.path.join(self.tmp, "docs", "visao-geral.md")))

    def test_fonte_que_nao_existe_sai_1_e_nao_escreve_nada(self):
        # Errar a pasta-fonte é errar onde o projeto inteiro vai morar. Criar
        # a pasta por conta própria esconderia o erro de digitação atrás de
        # uma árvore de arquivos no lugar errado.
        r = self._rodar("--fonte", "pasta-que-nao-existe")
        self.assertEqual(r.returncode, 1)
        self.assertFalse(
            os.path.exists(os.path.join(self.tmp, "pasta-que-nao-existe")))

    def test_visao_geral_sem_corpo_no_stdin_sai_1(self):
        # Pedir `--visao-geral -` e não mandar corpo é engano de quem chamou.
        # Escrever um arquivo vazio seria pior que recusar: a verificação do
        # gerador trata nota vazia como erro, e ele só apareceria lá na
        # frente, longe da causa.
        r = self._rodar("--fonte", "docs", "--visao-geral", "-", entrada="")
        self.assertEqual(r.returncode, 1)
        self.assertFalse(
            os.path.exists(os.path.join(self.tmp, "docs", "visao-geral.md")))

    def test_estrutura_faltando_e_aviso_e_nao_erro(self):
        # R19: erro e aviso se separam. Um arquivo do usuário sem a estrutura
        # que o protocolo lê é informação para ele decidir, não falha da
        # construção — se saísse 1, o passo 2 do Build pararia no meio de uma
        # entrevista por causa de um arquivo que está lá e é dele.
        self._escrever("docs/backlog.md", "# Backlog\n\nsem a seção.\n")
        r = self._rodar("--fonte", "docs")
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
