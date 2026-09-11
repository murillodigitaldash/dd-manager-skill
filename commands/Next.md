---
description: Pega o topo da fila de execução e entra nele.
argument-hint: "[item específico, se não quiser o topo da fila]"
---

Carregue o protocolo com a skill `dds`.

Resolva o contrato:

```sh
python3 "$CLAUDE_PLUGIN_ROOT/skills/dds/scripts/contrato.py"
```

Determine o próximo item da fila pelas quatro fontes do protocolo. Se o projeto
não declara `fonte.backlog`, a fila se lê pelos planos sem ledger e pelas
questões em aberto — diga isso ao usuário em vez de silenciar. Se o usuário
nomeou um item no argumento, use esse — mas avise se ele tiver dependência não
satisfeita, e diga qual.

Antes de começar, apresente em no máximo cinco linhas:

- **Item** — qual é, e de qual fase.
- **Por que agora** — dependência satisfeita, plano escrito, ou bloqueio caído.
- **Já existe plano?** — caminho do arquivo em `<artefatos.planos>`, ou "não".
- **Como pretendo tocar** — executar o plano existente, escrever um plano novo,
  ou resolver uma questão em aberto antes.

**Pare aqui e espere o usuário confirmar.** Só então entre no trabalho.

Ao confirmar, roteie para o caminho certo em vez de improvisar:

- plano escrito e não executado → `superpowers:subagent-driven-development`
- item sem plano → `superpowers:brainstorming`, depois `superpowers:writing-plans`
- bug ou teste falhando → `superpowers:systematic-debugging`

`superpowers` é recomendada, não obrigatória — se a skill de roteamento não
estiver disponível no projeto, não invoque uma skill inexistente: apresente o
item como acima e devolva a decisão de como tocá-lo ao usuário, em texto.

Não escreva no cérebro. Registrar o que foi feito é trabalho do `/dds:Save` e do
`/dds:End`.
