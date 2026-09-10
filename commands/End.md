---
description: Fecha o dia — grava o diário, promove o que virou conhecimento para a fonte, regenera o cérebro, commita e devolve o resumo.
---

Carregue o protocolo com a skill `dds`.

Resolva o contrato antes do passo 1 e use **esses** caminhos em todos eles:

```sh
python3 "$CLAUDE_PLUGIN_ROOT/skills/dds/scripts/contrato.py"
```

Execute os seis passos na ordem. Se um falhar, **pare e reporte** — não pule
para o seguinte.

### 1. Levantar o dia, por evidência

`git log --oneline` desde o último commit de ontem, `git status --short`, e o
`AAAA-MM-DD-sessao.md` de hoje se o `/dds:Save` já criou um. Memória não conta:
todo item precisa de arquivo, commit ou teste que o sustente.

### 2. Gravar o diário

Escreva ou atualize `<artefatos.diario>/AAAA-MM-DD-sessao.md` com as quatro
seções — Feito, Em andamento, Decidido, Aberto. É o que o `/dds:Start` vai ler
amanhã, então cada item de **Em andamento** precisa dizer onde parou.

### 3. Promover para a fonte

Só o que passou de "aconteceu hoje" para "o projeto agora sabe" sobe, e cada
tipo tem um destino declarado em `fonte`:

| O que emergiu | Onde gravar |
|---|---|
| Decisão arquitetural | um arquivo novo em `fonte.adrs`, no formato dos existentes, **mais** a linha no índice de `fonte.indice_adrs` e o contador do cabeçalho |
| Item de backlog entregue, lição da execução | `### Execução` na seção da fase em `fonte.backlog` |
| Questão em aberto respondida | marque `- [x]` no arquivo dentro de `fonte.questoes` e escreva a resposta abaixo — é zona semeada, edita direto |

Se o projeto não declara a chave de `fonte` que o conhecimento pede, **diga
isso** e deixe o item no diário, em vez de escolher um destino por conta.

Se o dia não produziu nenhum dos três, **não invente**: pule este passo e diga
que pulou.

Escrever em qualquer pasta de `zonas.reescrita` é erro — são reescritas na
próxima geração.

### 4. Regenerar com guarda

```sh
python3 "$CLAUDE_PLUGIN_ROOT/skills/dds/scripts/guarda.py"
```

Se ela recusar, ela diz o motivo e o conserto. Faça o conserto e rode de novo.
Nunca chame o gerador direto para contornar a guarda.

### 5. Commitar

Um commit, mensagem em português no padrão do repositório:

```
docs(cerebro): <o que o projeto passou a saber hoje>

<corpo: o que mudou na fonte e por quê>
```

Inclua o vault, o diário, e qualquer arquivo de `fonte` que tenha mudado.

### 6. Devolver o resumo

Só depois do commit, e nesta forma:

## Gravado no cérebro
Um bullet por promoção do passo 3, cada um nomeando o arquivo. Se nada subiu,
um bullet dizendo isso.

## Diário da sessão
Uma linha: caminho do arquivo e quantos itens em cada seção.

## Commit
O hash curto e a primeira linha da mensagem.

## Fila para a próxima sessão
Até seis bullets — o que ficou no topo, em tópicos secos.

Sem preâmbulo e sem fechamento. O resumo começa no primeiro título.
