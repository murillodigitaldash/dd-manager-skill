#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regeneração guardada do cérebro, para qualquer projeto.

O gerador apaga a zona reescrita antes de escrever. Isso é correto — ela é
espelho da fonte — e é também a forma mais fácil de perder trabalho: nota
editada à mão no vault, em vez de na fonte, some sem aviso na próxima geração.

Duas guardas em volta da geração:

  ANTES   se há edição não commitada numa zona reescrita, para. Aquilo é
          trabalho que existe só no vault, e precisa ir para a fonte primeiro.

  DEPOIS  se a geração apagou alguma nota, restaura o vault inteiro do git e
          para. Nota que some significa fonte incompleta, não vault errado.

As zonas vêm do contrato do projeto, nunca daqui. Este script não sabe o nome
de pasta nenhuma.

Uso:  python3 guarda.py [--raiz DIR]
      python3 guarda.py [--raiz DIR] --so-conferir    não regenera
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import contrato  # noqa: E402


def git(raiz, *args):
    # `core.quotepath=false` mantém o acento legível; sem ele o git devolve o
    # caminho em octal escapado, e a lista de erro fica ilegível.
    return subprocess.run(["git", "-c", "core.quotepath=false"] + list(args),
                          cwd=raiz, capture_output=True, text=True, check=False)


def estado(raiz, caminho_base):
    """Estado do git sob este caminho, como lista de (marca, arquivo).

    Para renames, o git devolve `R  antigo -> novo`, e devolvemos ambos
    os caminhos como entradas separadas, ambas com marca R.
    """
    saida = git(raiz, "status", "--porcelain", "--", caminho_base).stdout
    itens = []
    for linha in saida.split("\n"):
        if not linha.strip():
            continue
        marca = linha[:2].strip()
        resto = linha[3:].strip()

        # Se for rename, separa os dois caminhos
        if marca == "R" and " -> " in resto:
            # Ambos os lados podem estar entre aspas
            antigo, novo = resto.split(" -> ", 1)
            antigo = antigo.strip().strip('"')
            novo = novo.strip().strip('"')
            itens.append((marca, antigo))
            itens.append((marca, novo))
        else:
            arquivo = resto.strip('"')
            itens.append((marca, arquivo))
    return itens


def em_zona_reescrita(arquivo, vault, zonas_reescrita):
    prefixo = vault.rstrip("/") + "/"
    resto = arquivo[len(prefixo):] if arquivo.startswith(prefixo) else arquivo
    return any(resto == z or resto.startswith(z.rstrip("/") + "/") for z in zonas_reescrita)


def falhar(titulo, arquivos, conselho):
    print("\n✗ %s\n" % titulo)
    for a in arquivos:
        print("    %s" % a)
    print("\n%s\n" % conselho)
    return 1


def conferir_antes(raiz, c):
    # Regra inversa: qualquer status não vazio E não-ignorado é alteração. Enumeração
    # de códigos (M, A, D, R) já falhou duas vezes (faltaram R, e podem faltar outros
    # como C, U, T). Ignorado é `!!` e só aparece com --ignored. Sem --ignored, aqui
    # não chega, mas guardamos a regra: tudo que chega é trabalho a proteger.
    sujos = [a for marca, a in estado(raiz, c["vault"])
             if marca and marca != "!!"
             and em_zona_reescrita(a, c["vault"], c["zonas"]["reescrita"])]
    if sujos:
        return falhar(
            "Há edição não commitada em zona reescrita do cérebro.",
            sujos,
            "Regenerar apagaria isso. Leve o conteúdo para a fonte e rode de\n"
            "novo. Se a edição já veio da fonte, commite antes de regenerar.\n"
            "Se a marca for D (remoção em staged), commite a remoção primeiro —\n"
            "a guarda a lê como trabalho a perder.")
    return 0


def conferir_depois(raiz, c):
    # Procura por remoção: marca D (deleted) e R (renamed — que remove o caminho
    # antigo). estado() devolve ambos os caminhos para rename.
    apagados = [a for marca, a in estado(raiz, c["vault"]) if marca in ("D", "R")]
    if apagados:
        git(raiz, "checkout", "--", c["vault"])
        # Limpa apenas as zonas reescritas. É seguro por construção: conferir_antes
        # passou antes da geração, logo não havia nada não commitado nas zonas
        # reescritas; tudo que estiver não rastreado lá agora foi a geração que criou.
        # Não usamos git clean no vault inteiro, pois apagaria nota não commitada nas
        # zonas semeada e livre (trabalho do usuário que esta guarda existe para
        # proteger).
        # A limpeza é SEMPRE executada, mesmo se o apagado foi um diretório inteiro
        # (reportado como uma entrada só de diretório pelo git status).
        limpas = []
        for zona in c["zonas"]["reescrita"]:
            # Verifica existência contra a raiz (conferir_depois recebe raiz).
            # O git clean roda com cwd=raiz e interpreta caminho relativo certo.
            caminho_absoluto = os.path.join(raiz, c["vault"], zona)
            caminho_relativo = os.path.join(c["vault"], zona)
            if os.path.isdir(caminho_absoluto):
                r = git(raiz, "clean", "-fd", "--", caminho_relativo)
                if r.returncode == 0:
                    limpas.append(zona)
        return falhar(
            "A geração apagou notas. O cérebro foi restaurado do git.",
            ["Restaurado: %s" % a for a in apagados] +
            (["Residuo removido: %s" % z for z in limpas] if limpas else []),
            "Essas notas existem no vault e não na fonte. Devolva cada uma à\n"
            "fonte que a produz e rode de novo.")
    return 0


def main(argv):
    raiz = os.getcwd()
    if "--raiz" in argv:
        raiz = os.path.abspath(argv[argv.index("--raiz") + 1])

    try:
        c = contrato.ler(raiz)
    except contrato.ContratoInvalido as e:
        print("\n✗ %s\n" % e)
        return 1

    if c["origem_zonas"] == "escape":
        print("⚠ zonas lidas de .claude/dd.contrato.json, não do gerador.")

    if conferir_antes(raiz, c):
        return 1
    if "--so-conferir" in argv:
        print("✓ Nenhuma edição solta na zona reescrita.")
        return 0

    r = subprocess.run(c["gerador"], cwd=raiz, check=False)
    if r.returncode:
        print("\n✗ O gerador saiu com código %d. Nada foi conferido depois.\n"
              % r.returncode)
        return r.returncode

    if conferir_depois(raiz, c):
        return 1
    print("\n✓ Cérebro regenerado sem perder nota.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
