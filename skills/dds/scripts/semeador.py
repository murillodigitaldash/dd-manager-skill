#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Semeia a pasta-fonte de um projeto novo.

Isto é do plugin, não do projeto. O gerador do projeto semeia o **vault**; o
semeador semeia a **fonte**. Nenhum dos dois invade o outro, e é por isso que
este arquivo não mora dentro do `esqueleto_gerador.py`: aquele é copiado para
dentro do projeto e é do projeto para reescrever, então uma garantia posta
ali morre na primeira reescrita, sem aviso.

A garantia é uma só, e é o motivo deste arquivo existir: **a semeadura nunca
sobrescreve.** O que é do usuário não se recria por cima.

Uso:  python3 semeador.py --fonte <pasta>
      python3 semeador.py --fonte <pasta> --visao-geral -   (corpo no stdin)
"""

import json
import os
import sys

# Os nomes que este script escreve. Ficam aqui, e não espalhados pela prosa
# dos comandos, porque é daqui que `tests/test_agnostico.py` os lê para montar
# a allowlist de `.md` — um arquivo novo declarado aqui entra na allowlist
# sozinho, sem depender de alguém lembrar de estender uma lista à mão.
ARQUIVO_BACKLOG = "backlog.md"
ARQUIVO_ADRS = "adrs"
ARQUIVO_INDICE_ADRS = "indice.md"
ARQUIVO_VISAO_GERAL = "visao-geral.md"

BACKLOG = """# Backlog

Fila de execução deste projeto. Escreva aqui, e regenere — nunca no vault: a
zona reescrita é apagada e reescrita a cada geração.

## Fase 1

| # | Item | Depende de |
|---|---|---|

### Execução
"""

INDICE_ADRS = """# Índice de decisões arquiteturais

Uma decisão por arquivo nesta pasta, numerada em ordem. Escreva aqui, e
regenere — nunca no vault: a zona reescrita é apagada e reescrita a cada
geração.

Contador: 0
"""


# O que o protocolo lê dentro de cada arquivo, e para quê. Só estes dois têm
# exigência de estrutura, porque só destes dois o protocolo lê estrutura:
# `visao-geral.md` é documento espelhado como qualquer outro, e exigir forma
# dele seria o plugin prescrevendo o formato de um documento do projeto.
EXIGENCIAS = {
    ARQUIVO_BACKLOG: [
        ("### Execução", "a seção `### Execução`, de onde sai a fila de execução"),
    ],
    ARQUIVO_INDICE_ADRS: [
        ("Contador:", "a linha `Contador:` no cabeçalho, de onde sai a "
                      "numeração da próxima decisão"),
    ],
}


def semear_arquivo(caminho, corpo, exigencias=()):
    """Escreve `corpo` em `caminho` — mas só se ele ainda não existir.

    Três saídas, e só três:

      criado               não existia; nasceu com a estrutura do protocolo.
      preservado           já existia, com a estrutura que o protocolo lê.
      estrutura_incompleta já existia, sem ela. Não conserta: consertar é
                           reescrever o arquivo do usuário, que é a coisa
                           que este script existe para não fazer.
    """
    if os.path.exists(caminho):
        with open(caminho, encoding="utf-8") as f:
            texto = f.read()
        falta = [descricao for marcador, descricao in exigencias
                 if marcador not in texto]
        if falta:
            return {"caminho": caminho, "veredito": "estrutura_incompleta",
                    "falta": falta}
        return {"caminho": caminho, "veredito": "preservado"}
    pasta = os.path.dirname(caminho)
    if pasta:
        os.makedirs(pasta, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(corpo)
    return {"caminho": caminho, "veredito": "criado"}


def semear(fonte, visao_geral=None):
    arquivos = []
    if visao_geral is not None:
        # Sem exigência de estrutura: `visao-geral.md` é documento espelhado
        # como outro qualquer, e prescrever a forma dele seria o plugin
        # decidindo o formato de um documento do projeto.
        arquivos.append(semear_arquivo(
            os.path.join(fonte, ARQUIVO_VISAO_GERAL), visao_geral))
    arquivos.append(semear_arquivo(
        os.path.join(fonte, ARQUIVO_BACKLOG), BACKLOG,
        EXIGENCIAS[ARQUIVO_BACKLOG]))
    arquivos.append(semear_arquivo(
        os.path.join(fonte, ARQUIVO_ADRS, ARQUIVO_INDICE_ADRS),
        INDICE_ADRS, EXIGENCIAS[ARQUIVO_INDICE_ADRS]))
    return {"arquivos": arquivos}


def main(argv):
    if "--fonte" not in argv or argv.index("--fonte") + 1 >= len(argv):
        print("✗ Falta `--fonte <pasta>`: onde a documentação do projeto "
              "mora.", file=sys.stderr)
        return 1
    fonte = argv[argv.index("--fonte") + 1]
    if not os.path.isdir(fonte):
        print("\n✗ A pasta-fonte `%s` não existe. Não semeei nada.\n\n"
              "Não a criei por conta própria: errar a pasta-fonte é errar "
              "onde\no projeto inteiro vai morar, e criá-la esconderia o "
              "engano atrás\nde arquivos no lugar errado.\n" % fonte,
              file=sys.stderr)
        return 1

    visao_geral = None
    if "--visao-geral" in argv:
        visao_geral = sys.stdin.read()
        if not visao_geral.strip():
            print("\n✗ `--visao-geral` pediu o corpo pelo stdin e ele veio "
                  "vazio.\nNão semeei nada.\n\n"
                  "Um `%s` vazio é pior que ausente: a verificação do "
                  "gerador\ntrata nota vazia como erro, e ele apareceria "
                  "longe da causa.\n" % ARQUIVO_VISAO_GERAL, file=sys.stderr)
            return 1

    print(json.dumps(semear(fonte, visao_geral), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
