#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Projeto descartável para os testes: um repo git com gerador falso."""

import os
import subprocess

GERADOR_FALSO = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gerador falso: espelha fonte/*.md em vault/10 Espelho/."""
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
print("gerado")
'''

CONTRATO_MD = """---
vault: vault
gerador: python3 ferramentas/gerador.py
---

# O cerebro deste projeto

Espelha `fonte/` em `vault/`.
"""


def _escrever(caminho, texto):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(texto)


def git(raiz, *args):
    return subprocess.run(["git"] + list(args), cwd=raiz,
                          capture_output=True, text=True, check=False)


def projeto_fixture(raiz, com_contrato=True, com_git=True):
    """Monta em `raiz` um projeto com fonte, gerador falso e contrato."""
    _escrever(os.path.join(raiz, "fonte", "backlog.md"), "# Backlog\n\n- item\n")
    _escrever(os.path.join(raiz, "ferramentas", "gerador.py"), GERADOR_FALSO)
    if com_contrato:
        _escrever(os.path.join(raiz, ".claude", "dd.md"), CONTRATO_MD)
    if com_git:
        git(raiz, "init", "-b", "main")
        git(raiz, "config", "user.email", "teste@exemplo.com")
        git(raiz, "config", "user.name", "Teste")
        git(raiz, "add", "-A")
        git(raiz, "commit", "-m", "inicial")
    return raiz
