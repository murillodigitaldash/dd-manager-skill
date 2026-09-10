#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador do cérebro — versão mínima, escrita pelo /dds:Build.

Espelha uma pasta de documentação num vault Obsidian: uma nota por documento,
e os `[[links]]` que os documentos já trazem continuam valendo. A estrutura
de subpastas é preservada para evitar colisões de nome.

Aviso: links são sensíveis a maiúscula. `[[Nota]]` e `[[nota]]` são notas
diferentes. Documente esta regra ao orientar colaboradores sobre como escrever
a fonte.

Isto é ponto de partida, não produto final. Quando o projeto precisar de
ontologia — entidades próprias, grafo de dependência, notas derivadas de mais
de uma fonte — este arquivo é seu para reescrever. O que **não** muda é a
interface: a DDS depende de `--contrato`, e a guarda depende das três zonas.

Três zonas com regras diferentes de escrita:

  REESCRITA  apagada e reescrita a cada execução. É espelho da fonte.
  SEMEADA    criada se faltar, nunca sobrescrita. Suas respostas sobrevivem.
  LIVRE      o gerador nunca entra.

Uso:  python3 <este arquivo>              gera
      python3 <este arquivo> --contrato   imprime o contrato em JSON
      python3 <este arquivo> --verificar  confere sem escrever
      python3 <este arquivo> --semear     recria a zona semeada (só se faltar)
"""

import json
import os
import re
import shutil
import sys

# Este arquivo mora exatamente um nível abaixo da raiz do projeto (ex: ferramentas/).
# Se movido para outro nível, os caminhos se quebram sem aviso.
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── configuração ────────────────────────────────────────────────────────────
# O /dds:Build preenche estas quatro pela entrevista.
FONTE = "docs"                    # pasta da documentação-fonte
VAULT = "cerebro"                 # onde o vault nasce
ZONA_ESPELHO = "10 Documentos"    # a pasta reescrita, dentro do vault
PREREQUISITOS = ["docs"]          # sem isto não há o que espelhar
# ────────────────────────────────────────────────────────────────────────────

ZONA_SEMEADA = ["00 Mapas", "70 Decisões em aberto"]
ZONA_LIVRE = ["90 Notas"]

CONTRATO = {
    "zonas": {"reescrita": [ZONA_ESPELHO],
              "semeada": list(ZONA_SEMEADA),
              "livre": list(ZONA_LIVRE)},
    "fonte": {"documentos": FONTE,
              "questoes": os.path.join(VAULT, "70 Decisões em aberto")},
    "prerequisitos": list(PREREQUISITOS),
}

LINK = re.compile(r"\[\[([^\]|#]+)")


def caminho(*partes):
    return os.path.join(RAIZ, *partes)


def documentos():
    base = caminho(FONTE)
    achados = []
    for dirpath, _, nomes in os.walk(base):
        for nome in sorted(nomes):
            if nome.endswith(".md"):
                achados.append(os.path.join(dirpath, nome))
    return sorted(achados)


def conferir_prerequisitos():
    faltando = [p for p in PREREQUISITOS if not os.path.exists(caminho(p))]
    if faltando:
        print("\n✗ Falta o que espelhar. Não gerei nada.\n")
        for p in faltando:
            print("    %s" % p)
        print("\nO cérebro é espelho da fonte: sem estes, um vault gerado\n"
              "pareceria completo e não seria.\n")
        return 1
    return 0


def semear(forcar=False):
    for zona in ZONA_SEMEADA + ZONA_LIVRE:
        destino = caminho(VAULT, zona)
        if os.path.isdir(destino) and forcar:
            print("\n✗ `--semear` sobrescreveria `%s`, que já existe.\n" % zona)
            print("A zona semeada guarda o que a fonte não tem — as respostas\n"
                  "escritas direto no vault. Sobrescrever é perdê-las, e elas\n"
                  "não voltam na regeneração.\n\n"
                  "Se uma nota sumiu, o conserto é devolvê-la à fonte.\n")
            return 1
        os.makedirs(destino, exist_ok=True)
    indice = caminho(VAULT, "00 Mapas", "Índice.md")
    if not os.path.exists(indice):
        with open(indice, "w", encoding="utf-8") as f:
            f.write("# Índice\n\nMapa do cérebro. Esta nota é sua — o gerador\n"
                    "a cria uma vez e nunca mais a toca.\n")
    return 0


def gerar():
    if conferir_prerequisitos():
        return 1
    espelho = caminho(VAULT, ZONA_ESPELHO)
    if os.path.isdir(espelho):
        shutil.rmtree(espelho)
    os.makedirs(espelho)
    if semear():
        return 1
    fonte_abs = caminho(FONTE)
    docs = documentos()
    for doc in docs:
        with open(doc, encoding="utf-8") as f:
            corpo = f.read()
        # Preserve a estrutura de subpastas para evitar colisões de nome
        rel = os.path.relpath(doc, fonte_abs)
        destino = os.path.join(espelho, rel)
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "w", encoding="utf-8") as f:
            f.write(corpo)
    print("✓ %d notas espelhadas em %s/%s" % (
        len(docs), VAULT, ZONA_ESPELHO))
    return 0


def verificar():
    espelho = caminho(VAULT, ZONA_ESPELHO)
    if not os.path.isdir(espelho):
        print("✗ O vault não existe. Rode a geração antes.")
        return 1
    vault_abs = caminho(VAULT)
    # Duas estruturas de índice para duas perguntas diferentes:
    # 1. Exame completo de cada nota (sem colisão): chave = caminho relativo no vault
    notas_por_caminho = {}
    # 2. Resolução de links (como Obsidian): nome-base -> lista de caminhos
    nomes_base_para_caminhos = {}
    for dirpath, _, nomes in os.walk(vault_abs):
        for nome in nomes:
            if nome.endswith(".md"):
                caminho_completo = os.path.join(dirpath, nome)
                rel_vault = os.path.relpath(caminho_completo, vault_abs)
                nome_base = os.path.splitext(nome)[0]
                notas_por_caminho[rel_vault] = caminho_completo
                if nome_base not in nomes_base_para_caminhos:
                    nomes_base_para_caminhos[nome_base] = []
                nomes_base_para_caminhos[nome_base].append(rel_vault)
    # Conjuntos de nomes-base para detecção de ambiguidade
    nomes_base_unicos = set(nb for nb, caminhos in nomes_base_para_caminhos.items()
                            if len(caminhos) == 1)
    nomes_base_duplicados = set(nb for nb, caminhos in nomes_base_para_caminhos.items()
                                if len(caminhos) > 1)
    # Listas de problemas: erros vs avisos
    links_quebrados = []  # alvo não existe em lugar nenhum
    notas_vazias = []      # conteúdo vazio
    links_ambiguos = []    # alvo existe mas é ambíguo
    nomes_ambiguos = []    # nomes-base duplicados
    # Examinar todas as notas
    for rel_vault, arquivo in sorted(notas_por_caminho.items()):
        with open(arquivo, encoding="utf-8") as f:
            corpo = f.read()
        if not corpo.strip():
            notas_vazias.append(rel_vault)
        for alvo in LINK.findall(corpo):
            alvo_limpo = alvo.strip()
            if alvo_limpo in nomes_base_unicos:
                # Link válido — alvo existe e é único
                pass
            elif alvo_limpo in nomes_base_duplicados:
                # Alvo existe mas é ambíguo — aviso, não erro
                candidatos = nomes_base_para_caminhos[alvo_limpo]
                links_ambiguos.append("%s → [[%s]] (em: %s)" % (rel_vault, alvo_limpo,
                                                                 ", ".join(candidatos)))
            else:
                # Alvo não existe em lugar nenhum — erro
                links_quebrados.append("%s → [[%s]]" % (rel_vault, alvo_limpo))
    # Registrar nomes-base ambíguos
    for nome_base, caminhos in sorted(nomes_base_para_caminhos.items()):
        if len(caminhos) > 1:
            nomes_ambiguos.append("%s (em: %s)" % (nome_base, ", ".join(caminhos)))
    # Separar saída: erros vs avisos
    tem_erro = links_quebrados or notas_vazias
    tem_aviso = links_ambiguos or nomes_ambiguos
    if tem_erro:
        print("\n✗ Verificação encontrou erro.\n")
        for q in links_quebrados:
            print("    link quebrado: %s" % q)
        for v in notas_vazias:
            print("    nota vazia: %s" % v)
        print("")
    if tem_aviso:
        print("\n⚠ Verificação encontrou aviso.\n")
        for a in links_ambiguos:
            print("    link ambíguo: %s" % a)
        for a in nomes_ambiguos:
            print("    nome ambíguo: %s" % a)
        print("")
    if not tem_erro and not tem_aviso:
        print("✓ %d notas, nenhum link quebrado, nenhuma nota vazia, nenhuma ambiguidade." % len(notas_por_caminho))
    return 1 if tem_erro else 0


def main(argv):
    if "--contrato" in argv:
        print(json.dumps(CONTRATO, ensure_ascii=False))
        return 0
    if "--verificar" in argv:
        return verificar()
    if "--semear" in argv:
        return semear(forcar=True)
    return gerar()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
