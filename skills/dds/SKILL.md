---
name: dds
description: Protocolo do cérebro de um projeto — onde mora a fila de execução, o que ler para montar o retrospecto do dia, e como devolver o trabalho à fonte sem perder nota na regeneração. Use ao rodar qualquer comando /dds:, ou quando precisar responder "o que já foi feito e o que falta".
---

# Protocolo do cérebro

O cérebro é um vault Obsidian **gerado** a partir da documentação do
repositório. Ele não é a fonte: é o espelho dela.

Onde o vault fica e quem o gera muda de projeto para projeto. **Nada neste
protocolo é um caminho fixo** — tudo vem do contrato.

## Primeiro, resolva o contrato

```sh
python3 "$CLAUDE_PLUGIN_ROOT/skills/dds/scripts/contrato.py"
```

Devolve, em JSON:

| Chave | O que é |
|---|---|
| `vault` | pasta do vault, relativa à raiz |
| `gerador` | o comando que gera, como lista |
| `zonas.reescrita` | pastas apagadas e reescritas a cada geração |
| `zonas.semeada` | criadas uma vez, nunca sobrescritas |
| `zonas.livre` | o gerador nunca entra |
| `fonte` | onde mora cada tipo de conhecimento na documentação-fonte |
| `prerequisitos` | o que precisa existir para haver o que espelhar |
| `artefatos` | diário, planos e specs |
| `origem_zonas` | `"gerador"` no caminho normal; `"escape"` quando o gerador não responde `--contrato` e as zonas vieram de `.claude/dd.contrato.json` — o `/dds:Build` manda conferir isto ao escrever um gerador novo |

Se ele falhar, pare e reporte. Sem contrato não há projeto para ler — e o
conserto é `/dds:Build`, não adivinhar caminho.

## A regra que organiza tudo

O gerador **apaga e reescreve** as pastas de `zonas.reescrita` a cada
execução. Escrever ali é perder o texto na próxima geração.

**Para gravar conhecimento novo, escreva na fonte e regenere.**

Duas zonas escapam disso, e só nelas se edita direto:

| Zona | Regra |
|---|---|
| `zonas.semeada` | criada uma vez, nunca sobrescrita — é onde moram as respostas que a fonte não tem |
| `zonas.livre` | o gerador não entra |

## Onde cada coisa mora

`fonte` mapeia o tipo de conhecimento ao arquivo que o guarda. As chaves que a
DDS usa, quando o projeto as declara:

| Chave de `fonte` | O que guarda | Quem escreve nela |
|---|---|---|
| `documentos` | a pasta-fonte inteira, espelhada nota a nota | qualquer commit na fonte — é o que o gerador lê para montar `zonas.reescrita` |
| `backlog` | situação da fase e itens entregues | `/dds:End`, passo de promoção |
| `adrs` | uma decisão arquitetural por arquivo | `/dds:End` |
| `indice_adrs` | o índice e o contador dos ADRs | `/dds:End`, junto com o ADR |
| `questoes` | questões em aberto, marcadas ao fechar | `/dds:End` — é zona semeada, edita direto |

Chave que o projeto não declara é assunto que ele não tem. Não invente destino
— se uma dessas chaves não fizer sentido para o projeto, remova-a do
`CONTRATO` do gerador em vez de apontar para um arquivo que não existe.

Os artefatos da DDS, que ela prescreve e o contrato pode sobrescrever:

| Artefato | Padrão |
|---|---|
| Diário da sessão | `<artefatos.diario>/AAAA-MM-DD-sessao.md` |
| Ledger de execução | `<artefatos.diario>/AAAA-MM-DD-<fase>-<plano>-ledger.md` |
| Plano de trabalho | `<artefatos.planos>/AAAA-MM-DD-*.md` |
| Spec | `<artefatos.specs>/AAAA-MM-DD-*.md` |

Nenhum comando `dds` escreve o ledger — quem o produz é o ecossistema
`superpowers` (`subagent-driven-development`), ao executar um plano. Sem essa
skill instalada, planos ficam sem ledger e a fila (item 3, abaixo) não
distingue "executado" de "ainda não". Recomendada, não obrigatória — ver
README.

Se os caminhos de `artefatos` caírem dentro da pasta que o gerador espelha —
caso comum quando a documentação-fonte é `docs/` e os padrões acima também
moram lá —, o diário, o ledger, os planos e as specs viram notas do vault
também, como qualquer outro documento da fonte. Isso é aceitável: nenhum
tratamento especial é necessário. Quem não quiser esse espelhamento
sobrescreve `diario`, `planos` e `specs` no frontmatter do contrato, apontando
para fora da fonte — a plugin já lê essas chaves de lá.

## A fila de execução

Não existe um arquivo "fila". Ela se lê cruzando quatro coisas, nesta ordem de
precedência:

1. **`### Execução` na seção da fase corrente** em `fonte.backlog` — o que já
   foi entregue, e o que não estava no backlog e foi feito assim mesmo.
2. **A tabela de backlog da mesma seção** — os itens numerados da fase, com
   dependências. O que não aparece como entregue no item 1 está aberto.
3. **Os `- [ ]` do plano mais recente** em `artefatos.planos` sem ledger
   correspondente em `artefatos.diario` — plano escrito e não executado é o
   topo da fila.
4. **A zona semeada de questões** (`fonte.questoes`) — questão `- [ ]` que
   bloqueia um item da fila.

Um plano com ledger foi executado. Um plano sem ledger está na fila.

Se o projeto não declara `fonte.backlog`, a fila se lê só pelos itens 3 e 4 —
e diga isso ao usuário em vez de silenciar.

## Regenerar

Sempre pela guarda, **nunca** chamando o gerador direto:

```sh
python3 "$CLAUDE_PLUGIN_ROOT/skills/dds/scripts/guarda.py"
```

`--so-conferir` roda só a guarda de antes e não gera nada — útil para saber se
há edição solta em zona reescrita sem disparar uma regeneração.

Ela põe duas guardas:

- **antes** — recusa se há edição não commitada em zona reescrita, porque
  regenerar apagaria esse trabalho;
- **depois** — se a geração apagou alguma nota, restaura o vault do git e
  para, nomeando o que sumiu.

Nota que some tem duas causas possíveis, e a guarda nomeia as duas: **fonte
incompleta** — devolva o conteúdo à fonte que o produz e rode de novo — ou
**documento removido de propósito** — devolvê-lo desfaria a remoção; o
conserto aí é commitar a remoção no vault e rodar de novo.

## Convenções

- Tudo em português: notas, mensagens de commit, comentários.
- Data absoluta, nunca relativa. "2026-09-10", não "ontem".
- Mensagem de commit do cérebro: `docs(cerebro): <o que mudou>`.
- Bullet de retrospecto é tópico, não parágrafo. Uma linha, sem subordinada.
