#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resolve o contrato de um projeto.

O contrato tem duas partes, e a divisão é deliberada:

    .claude/dd.md            frontmatter plano — o que um humano escreve
    <gerador> --contrato     JSON — o que o gerador sabe sobre si mesmo

As zonas, o mapa da fonte e os pré-requisitos vêm sempre do gerador.
Declará-los também no frontmatter criaria duas fontes para o mesmo fato — e
duas fontes divergem. É o defeito que este desenho existe para não repetir.

Escape: gerador que não responde `--contrato`. Aí, e só aí, lê-se
`.claude/dd.contrato.json`, com o mesmo formato. Isso devolve a duplicação, e
por isso é escape, não caminho.

Uso:  python3 contrato.py [--raiz DIR]     imprime o contrato resolvido
"""

import json
import os
import shlex
import subprocess
import sys

# Artefatos da DDS, não do domínio do projeto — então ela pode prescrevê-los.
# O frontmatter sobrescreve, para o projeto que já tenha outro layout.
ARTEFATOS_PADRAO = {
    "diario": "docs/superpowers/execucao",
    "planos": "docs/superpowers/plans",
    "specs": "docs/superpowers/specs",
}

ZONAS_EXIGIDAS = ("reescrita", "semeada", "livre")

# O arquivo de contrato, declarado onde é lido. O nome fica numa constante,
# e não solto no meio do código, porque `tests/test_agnostico.py` deriva a
# allowlist de `.md` das constantes `ARQUIVO_*` dos scripts do plugin — um
# arquivo próprio da DDS declarado assim entra na allowlist sozinho.
PASTA_CONTRATO = ".claude"
ARQUIVO_CONTRATO = "dd.md"


class ContratoInvalido(Exception):
    """Contrato ausente, incompleto ou incoerente. A mensagem diz o conserto."""


def ler_frontmatter(texto):
    """Frontmatter plano: `chave: valor`, uma por linha, entre `---`."""
    linhas = texto.split("\n")
    if not linhas or linhas[0].strip() != "---":
        raise ContratoInvalido(
            "O contrato precisa começar com uma linha `---`.\n"
            "Formato:\n\n---\nvault: <pasta do vault>\n"
            "gerador: <comando que gera>\n---")
    campos = {}
    for i, linha in enumerate(linhas[1:], start=1):
        if linha.strip() == "---":
            return campos
        if not linha.strip() or linha.lstrip().startswith("#"):
            continue
        if ":" not in linha:
            raise ContratoInvalido(
                "Linha %d do frontmatter não é `chave: valor`: %r" % (i + 1, linha))
        chave, valor = linha.split(":", 1)
        campos[chave.strip()] = valor.strip()
    raise ContratoInvalido("O frontmatter não foi fechado com `---`.")


def _perguntar_ao_gerador(raiz, comando):
    """Executa gerador com --contrato. Devolve (bruto, sucesso).

    Se sucesso for True, bruto é o JSON parseado (pode ser None, [], etc).
    Se sucesso for False, bruto é irrelevante e há uma chave 'motivo' levantada
    em exceção ContratoInvalido pelo caller.
    """
    try:
        r = subprocess.run(comando + ["--contrato"], cwd=raiz,
                           capture_output=True, text=True, check=False)
    except OSError as e:
        return None, False, "não foi possível executar %r: %s" % (" ".join(comando), e)
    if r.returncode != 0:
        return None, False, "`%s --contrato` saiu com código %d" % (
            " ".join(comando), r.returncode)
    try:
        bruto = json.loads(r.stdout)
    except ValueError as e:
        return None, False, "`%s --contrato` não devolveu JSON válido: %s" % (
            " ".join(comando), e)
    return bruto, True, None


def _validar(bruto, origem):
    if not isinstance(bruto, dict):
        raise ContratoInvalido("O contrato de %s não é um objeto JSON." % origem)
    zonas = bruto.get("zonas")
    if not isinstance(zonas, dict):
        raise ContratoInvalido("O contrato de %s não tem `zonas`." % origem)
    for nome in ZONAS_EXIGIDAS:
        if nome not in zonas:
            raise ContratoInvalido(
                "O contrato de %s não declara a zona `%s`.\n"
                "As três são obrigatórias: %s." % (
                    origem, nome, ", ".join(ZONAS_EXIGIDAS)))
        if not isinstance(zonas[nome], list):
            raise ContratoInvalido(
                "A zona `%s` do contrato de %s não é uma lista." % (nome, origem))
    fonte = bruto.get("fonte", {})
    if not isinstance(fonte, dict):
        raise ContratoInvalido("`fonte` do contrato de %s não é um objeto." % origem)
    prerequisitos = bruto.get("prerequisitos", [])
    if not isinstance(prerequisitos, list):
        raise ContratoInvalido(
            "`prerequisitos` do contrato de %s não é uma lista." % origem)
    return {"zonas": {n: list(zonas[n]) for n in ZONAS_EXIGIDAS},
            "fonte": dict(fonte),
            "prerequisitos": list(prerequisitos)}


def ler(raiz):
    """Devolve o contrato resolvido do projeto em `raiz`."""
    caminho = os.path.join(raiz, PASTA_CONTRATO, ARQUIVO_CONTRATO)
    if not os.path.isfile(caminho):
        raise ContratoInvalido(
            "Este projeto não tem contrato: falta `.claude/dd.md`.\n"
            "Rode /dds:Build para criá-lo.")
    with open(caminho, encoding="utf-8") as f:
        campos = ler_frontmatter(f.read())

    for chave in ("vault", "gerador"):
        if not campos.get(chave):
            raise ContratoInvalido(
                "`.claude/dd.md` não declara `%s`.\n"
                "As duas chaves obrigatórias são `vault` e `gerador`." % chave)

    try:
        comando = shlex.split(campos["gerador"])
    except ValueError as e:
        raise ContratoInvalido(
            "Não consegui fazer parse do comando `gerador`: %r\n"
            "Problema: %s\n"
            "Conserto: feche as aspas ou escape corretamente." % (campos["gerador"], e))
    bruto, sucesso, motivo = _perguntar_ao_gerador(raiz, comando)
    origem_zonas = "gerador"

    if not sucesso:
        escape = os.path.join(raiz, ".claude", "dd.contrato.json")
        if not os.path.isfile(escape):
            raise ContratoInvalido(
                "O gerador não respondeu `--contrato` (%s), e não há escape.\n"
                "Conserto preferido: fazer o gerador imprimir o JSON do "
                "contrato quando receber `--contrato`.\n"
                "Escape: escrever `.claude/dd.contrato.json` com o mesmo "
                "formato — ao custo de declarar as zonas em dois lugares." % motivo)
        with open(escape, encoding="utf-8") as f:
            try:
                bruto = json.load(f)
            except ValueError as e:
                raise ContratoInvalido(
                    "`.claude/dd.contrato.json` não é JSON válido: %s" % e)
        origem_zonas = "escape"

    resolvido = _validar(bruto, origem_zonas)
    artefatos = dict(ARTEFATOS_PADRAO)
    for chave in ARTEFATOS_PADRAO:
        if campos.get(chave):
            artefatos[chave] = campos[chave]

    resolvido.update({"vault": campos["vault"],
                      "gerador": comando,
                      "artefatos": artefatos,
                      "origem_zonas": origem_zonas})
    return resolvido


def main(argv):
    raiz = os.getcwd()
    if "--raiz" in argv:
        raiz = argv[argv.index("--raiz") + 1]
    try:
        print(json.dumps(ler(raiz), ensure_ascii=False, indent=2))
    except ContratoInvalido as e:
        sys.stderr.write("\n✗ %s\n\n" % e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
