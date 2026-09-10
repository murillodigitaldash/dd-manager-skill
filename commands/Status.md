---
description: A fila de execução e a situação das fases, sem retrospecto de sessão.
---

Carregue o protocolo com a skill `dds`.

Resolva o contrato:

```sh
python3 "$CLAUDE_PLUGIN_ROOT/skills/dds/scripts/contrato.py"
```

Leia a fila de execução pelas quatro fontes que o protocolo lista e devolva:

## Fase corrente
Uma linha: número, nome e quantos itens do backlog estão entregues de quantos.
Se o projeto não declara `fonte.backlog`, diga que a fase não é legível e siga
para as outras seções com o que os planos mostram.

## Entregue
Os itens do backlog da fase já concluídos, um por linha. Se o projeto não
declara `fonte.backlog`, diga que o backlog não é legível — com um único bullet.

## Aberto
Os itens do backlog ainda não começados, com a dependência de cada um quando
ela ainda não estiver satisfeita. Se o projeto não declara `fonte.backlog`, diga
que o backlog não é legível — com um único bullet. Mas `## Topo da fila`
continua valendo, porque se lê dos planos sem ledger.

## Topo da fila
O próximo item a executar, e por que é ele — dependência satisfeita, plano já
escrito, ou bloqueio removido.

Tópicos secos, uma linha cada. Sem preâmbulo. Este comando só lê: não altere
arquivo nem commite.
