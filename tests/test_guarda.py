#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUARDA = os.path.join(RAIZ, "skills", "dds", "scripts", "guarda.py")
sys.path.insert(0, os.path.join(RAIZ, "tests"))

import apoio  # noqa: E402


def rodar(raiz, *args):
    return subprocess.run([sys.executable, GUARDA, "--raiz", raiz] + list(args),
                          capture_output=True, text=True, check=False)


class TestGuarda(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        apoio.projeto_fixture(self.tmp)

    def _gerar_e_commitar(self):
        r = rodar(self.tmp)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        apoio.git(self.tmp, "add", "-A")
        apoio.git(self.tmp, "commit", "-m", "vault")

    def test_primeira_geracao_funciona(self):
        r = rodar(self.tmp)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(os.path.isfile(
            os.path.join(self.tmp, "vault", "10 Espelho", "backlog.md")))

    def test_recusa_com_edicao_solta_em_zona_reescrita(self):
        self._gerar_e_commitar()
        alvo = os.path.join(self.tmp, "vault", "10 Espelho", "backlog.md")
        with open(alvo, "a", encoding="utf-8") as f:
            f.write("\nescrito a mao\n")
        r = rodar(self.tmp)
        self.assertEqual(r.returncode, 1)
        self.assertIn("10 Espelho/backlog.md", r.stdout)
        self.assertIn("fonte", r.stdout.lower())

    def test_edicao_em_zona_semeada_nao_bloqueia(self):
        self._gerar_e_commitar()
        alvo = os.path.join(self.tmp, "vault", "00 Mapas", "Indice.md")
        with open(alvo, "a", encoding="utf-8") as f:
            f.write("\nminha resposta\n")
        r = rodar(self.tmp)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(alvo, encoding="utf-8") as f:
            self.assertIn("minha resposta", f.read())

    def test_edicao_em_zona_livre_nao_bloqueia(self):
        self._gerar_e_commitar()
        nota = os.path.join(self.tmp, "vault", "90 Notas", "ideia.md")
        with open(nota, "w", encoding="utf-8") as f:
            f.write("# ideia\n")
        r = rodar(self.tmp)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(os.path.isfile(nota))

    def test_restaura_quando_a_geracao_apaga_nota(self):
        self._gerar_e_commitar()
        # A fonte encolhe: o documento some, e com ele a nota espelhada.
        os.remove(os.path.join(self.tmp, "fonte", "backlog.md"))
        apoio.git(self.tmp, "add", "-A")
        apoio.git(self.tmp, "commit", "-m", "fonte encolheu")
        r = rodar(self.tmp)
        self.assertEqual(r.returncode, 1)
        self.assertIn("backlog.md", r.stdout)
        # O vault voltou ao que estava commitado.
        self.assertTrue(os.path.isfile(
            os.path.join(self.tmp, "vault", "10 Espelho", "backlog.md")))

    def test_restauracao_nomeia_as_duas_causas_possiveis(self):
        # A nota que some pode ter duas causas — fonte incompleta, ou remoção
        # de propósito — e a mensagem precisa nomear as duas em vez de supor
        # sempre a primeira (conselho invertido quando a remoção foi
        # intencional: devolver desfaria o que o usuário quis).
        self._gerar_e_commitar()
        os.remove(os.path.join(self.tmp, "fonte", "backlog.md"))
        apoio.git(self.tmp, "add", "-A")
        apoio.git(self.tmp, "commit", "-m", "fonte encolheu")
        r = rodar(self.tmp)
        self.assertEqual(r.returncode, 1)
        saida = r.stdout + r.stderr
        self.assertIn("fonte", saida.lower())
        self.assertIn("propósito", saida.lower())
        self.assertIn("commit", saida.lower())

    def test_restauracao_sem_residuo_nao_anuncia_limpeza(self):
        # Mesma restauração do teste acima, mas aqui a geração não deixa
        # nenhum arquivo não rastreado na zona reescrita: o `git checkout`
        # já devolve a pasta ao estado commitado, e o `git clean` que roda
        # depois não tem nada para remover. "Residuo removido" é uma alegação
        # de trabalho feito — não pode aparecer quando o git clean não fez
        # nada, mesmo saindo com código 0.
        self._gerar_e_commitar()
        os.remove(os.path.join(self.tmp, "fonte", "backlog.md"))
        apoio.git(self.tmp, "add", "-A")
        apoio.git(self.tmp, "commit", "-m", "fonte encolheu")
        r = rodar(self.tmp)
        self.assertEqual(r.returncode, 1)
        self.assertIn("backlog.md", r.stdout)
        self.assertNotIn("Residuo removido", r.stdout)

    def test_so_conferir_nao_gera(self):
        r = rodar(self.tmp, "--so-conferir")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse(os.path.isdir(os.path.join(self.tmp, "vault")))

    def test_sem_contrato_falha_dizendo_o_conserto(self):
        os.remove(os.path.join(self.tmp, ".claude", "dd.md"))
        r = rodar(self.tmp)
        self.assertEqual(r.returncode, 1)
        self.assertIn("/dds:Build", r.stdout + r.stderr)

    def test_colisao_de_prefixo_em_zona(self):
        # Testa que uma zona "10 Espelho Extra" (livre) não bloqueia edição mesmo
        # com zona reescrita "10 Espelho" existindo. Sem delimitador de diretório,
        # o prefixo "10 Espelho" casaria com "10 Espelho Extra/...".
        gerador_colisao = '''#!/usr/bin/env python3
import json, os, sys
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAULT = os.path.join(RAIZ, "vault")
CONTRATO = {
    "zonas": {"reescrita": ["10 Espelho"],
              "semeada": ["00 Mapas"],
              "livre": ["10 Espelho Extra", "90 Notas"]},
    "fonte": {"backlog": "fonte/backlog.md"},
    "prerequisitos": ["fonte/backlog.md"],
}
if "--contrato" in sys.argv:
    print(json.dumps(CONTRATO, ensure_ascii=False))
    sys.exit(0)
reescrita = os.path.join(VAULT, "10 Espelho")
if os.path.isdir(reescrita):
    for nome in os.listdir(reescrita):
        os.remove(os.path.join(reescrita, nome))
for zona in ("10 Espelho", "00 Mapas", "10 Espelho Extra", "90 Notas"):
    os.makedirs(os.path.join(VAULT, zona), exist_ok=True)
fonte = os.path.join(RAIZ, "fonte")
for nome in sorted(os.listdir(fonte)):
    if not nome.endswith(".md"):
        continue
    with open(os.path.join(fonte, nome), encoding="utf-8") as f:
        corpo = f.read()
    destino = os.path.join(reescrita, nome)
    with open(destino, "w", encoding="utf-8") as f:
        f.write(corpo)
semente = os.path.join(VAULT, "00 Mapas", "Indice.md")
if not os.path.exists(semente):
    with open(semente, "w", encoding="utf-8") as f:
        f.write("# Indice\\n")
print("gerado")
'''
        # Escreve gerador falso com zonas que colidem por prefixo
        gerador_path = os.path.join(self.tmp, "ferramentas", "gerador.py")
        with open(gerador_path, "w", encoding="utf-8") as f:
            f.write(gerador_colisao)

        # Gera e commita
        r = rodar(self.tmp)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        apoio.git(self.tmp, "add", "-A")
        apoio.git(self.tmp, "commit", "-m", "vault")

        # Edita em "10 Espelho Extra" (zona livre, não deveria bloquear)
        nota = os.path.join(self.tmp, "vault", "10 Espelho Extra", "pessoal.md")
        with open(nota, "w", encoding="utf-8") as f:
            f.write("# Meu trabalho\n")

        # Regenera — deveria passar
        r = rodar(self.tmp)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # E a nota em zona livre deve ter sobrevivido
        self.assertTrue(os.path.isfile(nota))

    def test_nota_nao_commitada_em_zona_livre_sobrevive_restauracao(self):
        # Testa que notas não commitadas em zonas semeada e livre sobrevivem a
        # uma restauração disparada por nota apagada em zona reescrita.
        self._gerar_e_commitar()

        # Adiciona nota não commitada em zona semeada
        nota_semeada = os.path.join(self.tmp, "vault", "00 Mapas", "decisao.md")
        with open(nota_semeada, "w", encoding="utf-8") as f:
            f.write("# Decisão não commitada\n")

        # Adiciona nota não commitada em zona livre
        nota_livre = os.path.join(self.tmp, "vault", "90 Notas", "ideia.md")
        with open(nota_livre, "w", encoding="utf-8") as f:
            f.write("# Ideia não commitada\n")

        # A fonte encolhe, disparando restauração
        os.remove(os.path.join(self.tmp, "fonte", "backlog.md"))
        apoio.git(self.tmp, "add", "-A")
        apoio.git(self.tmp, "commit", "-m", "fonte encolheu")

        # Regenera — deve recusar por conta da nota apagada
        r = rodar(self.tmp)
        self.assertEqual(r.returncode, 1)
        self.assertIn("backlog.md", r.stdout)

        # As notas não commitadas devem ter sobrevivido à restauração
        self.assertTrue(os.path.isfile(nota_semeada),
                       "Nota em zona semeada foi apagada na restauração")
        self.assertTrue(os.path.isfile(nota_livre),
                       "Nota em zona livre foi apagada na restauração")
        with open(nota_semeada, encoding="utf-8") as f:
            self.assertIn("Decisão", f.read())
        with open(nota_livre, encoding="utf-8") as f:
            self.assertIn("Ideia", f.read())

    def test_residuo_nao_rastreado_e_removido(self):
        # Testa que resíduo não rastreado criado pela geração em zona reescrita é
        # removido após restauração por nota apagada. Nota que rodar() não passa cwd=,
        # então testa com cwd ≠ raiz (o caso difícil).

        # Gerador que planta resíduo apenas quando fonte está vazia (simula
        # comportamento de gerador bugado)
        gerador_residuo = '''#!/usr/bin/env python3
import json, os, sys
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAULT = os.path.join(RAIZ, "vault")
CONTRATO = {
    "zonas": {"reescrita": ["10 Espelho"],
              "semeada": ["00 Mapas"],
              "livre": ["90 Notas"]},
    "fonte": {"backlog": "fonte/backlog.md"},
    "prerequisitos": ["fonte/backlog.md"],
}
if "--contrato" in sys.argv:
    print(json.dumps(CONTRATO, ensure_ascii=False))
    sys.exit(0)

reescrita = os.path.join(VAULT, "10 Espelho")
if os.path.isdir(reescrita):
    for nome in os.listdir(reescrita):
        os.remove(os.path.join(reescrita, nome))
for zona in ("10 Espelho", "00 Mapas", "90 Notas"):
    os.makedirs(os.path.join(VAULT, zona), exist_ok=True)

fonte = os.path.join(RAIZ, "fonte")
for nome in sorted(os.listdir(fonte)):
    if not nome.endswith(".md"):
        continue
    with open(os.path.join(fonte, nome), encoding="utf-8") as f:
        corpo = f.read()
    destino = os.path.join(reescrita, nome)
    with open(destino, "w", encoding="utf-8") as f:
        f.write(corpo)

semente = os.path.join(VAULT, "00 Mapas", "Indice.md")
if not os.path.exists(semente):
    with open(semente, "w", encoding="utf-8") as f:
        f.write("# Indice\\n")

# Planta residuo apenas se nao ha backlog na fonte (simula bug)
if not os.path.exists(os.path.join(fonte, "backlog.md")):
    residuo = os.path.join(reescrita, "novo.md")
    with open(residuo, "w", encoding="utf-8") as f:
        f.write("# Residuo\\n")

print("gerado")
'''
        gerador_path = os.path.join(self.tmp, "ferramentas", "gerador.py")
        with open(gerador_path, "w", encoding="utf-8") as f:
            f.write(gerador_residuo)

        # Gera e commita uma primeira vez (sem resíduo)
        r = rodar(self.tmp)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        apoio.git(self.tmp, "add", "-A")
        apoio.git(self.tmp, "commit", "-m", "vault inicial")

        # Remove a fonte para disparar resíduo na próxima geração
        os.remove(os.path.join(self.tmp, "fonte", "backlog.md"))
        apoio.git(self.tmp, "add", "-A")
        apoio.git(self.tmp, "commit", "-m", "fonte encolheu")

        # Regenera — gerador vai apagar backlog.md e plantar novo.md
        r = rodar(self.tmp)
        self.assertEqual(r.returncode, 1)
        self.assertIn("backlog.md", r.stdout)

        # A nota apagada deve ter voltado
        self.assertTrue(os.path.isfile(
            os.path.join(self.tmp, "vault", "10 Espelho", "backlog.md")))

        # E o resíduo deve ter sumido (git clean rodou)
        residuo_path = os.path.join(self.tmp, "vault", "10 Espelho", "novo.md")
        self.assertFalse(os.path.isfile(residuo_path),
                        "Resíduo não rastreado não foi removido")

        # A saída deve mencionar "Residuo removido"
        self.assertIn("Residuo removido", r.stdout)

    def test_rename_em_zona_reescrita_bloqueia(self):
        # Testa que um rename (git mv) em zona reescrita é detectado e bloqueia.
        # Historicamente, R (rename) não era checado (o revisor reproduziu).
        self._gerar_e_commitar()

        alvo = os.path.join(self.tmp, "vault", "10 Espelho", "backlog.md")
        novo = os.path.join(self.tmp, "vault", "10 Espelho", "roteiro.md")

        # Faz rename via git mv
        r = apoio.git(self.tmp, "mv", alvo, novo)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

        # Tenta regenerar
        r = rodar(self.tmp)
        self.assertEqual(r.returncode, 1)

        # Deve nomear os dois lados do rename de forma legível
        # (em zona reescrita "10 Espelho/...")
        output = r.stdout
        self.assertIn("10 Espelho", output,
                     "Rename não nomeou a zona reescrita de forma legível")


if __name__ == "__main__":
    unittest.main()
