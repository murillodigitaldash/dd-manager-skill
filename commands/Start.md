---
description: Abre a sessão — lê o cérebro e devolve o retrospecto da última sessão e a fila de hoje, em tópicos.
---

Carregue o protocolo com a skill `dds` antes de qualquer outra coisa.

Resolva o contrato e use **esses** caminhos daqui em diante:

```sh
python3 "$CLAUDE_PLUGIN_ROOT/skills/dds/scripts/contrato.py"
```

Se ele falhar, pare e reporte — o conserto é `/dds:Build`, não adivinhar
caminho.

Depois levante, **sem escrever nada**:

1. **A última sessão.** O arquivo mais recente que casa
   `<artefatos.diario>/*-sessao.md`. Se não houver nenhum, use
   `git log --oneline --since="7 days ago"` e os ledgers mais recentes.
2. **A situação das fases.** As seções `### Execução` de `fonte.backlog`. Se o
   projeto não declara `backlog`, diga isso e siga sem inventar.
3. **A fila.** Os planos em `<artefatos.planos>` sem ledger correspondente em
   `<artefatos.diario>`, e seus `- [ ]` abertos.
4. **O que está solto.** `git status --short`, a branch atual, e commits ainda
   não enviados (`git log --oneline @{u}..` — se não houver upstream, diga
   isso em vez de falhar).

Então responda **exatamente** com estes quatro tópicos, nesta ordem:

## Concluídos na última sessão
## Pendentes de revisão para hoje
## Pendentes de execução para hoje
## Backlog dos próximos dias

Regras da resposta, que valem mais que a completude:

- **Bullet é tópico, não parágrafo.** Uma linha por item, sem oração
  subordinada, sem justificativa. Se precisar explicar, o item está errado.
- **Nada de preâmbulo nem de fechamento.** Comece no primeiro título e termine
  no último bullet.
- **Seção vazia se diz vazia**, com um único bullet — não invente item para
  preencher.
- Máximo de seis bullets por seção. Passando disso, agrupe.
- "Pendentes de revisão" é o que foi feito e ainda não foi conferido, mesclado
  ou enviado. "Pendentes de execução" é o que está no topo da fila para hoje.

Não execute nada, não altere arquivo, não commite. Este comando só lê.
