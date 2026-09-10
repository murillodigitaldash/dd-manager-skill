---
description: Checkpoint no meio da sessão — grava o diário do dia sem regenerar o cérebro nem commitar.
argument-hint: "[nota livre sobre o ponto em que parou]"
---

Carregue o protocolo com a skill `dds`.

Resolva o contrato:

```sh
python3 "$CLAUDE_PLUGIN_ROOT/skills/dds/scripts/contrato.py"
```

Grave o estado atual da sessão em `<artefatos.diario>/AAAA-MM-DD-sessao.md`
(data de hoje). Se o arquivo já existir, **atualize-o** — não crie um segundo.

Levante o que aconteceu até agora por evidência, não por memória:
`git log --oneline` do dia, `git status --short`, e os arquivos que a sessão
tocou.

Estrutura do arquivo:

```markdown
# Sessão de AAAA-MM-DD

## Feito
## Em andamento
## Decidido
## Aberto
```

- **Feito** — o que está concluído e verificado. Cada item nomeia a evidência
  (teste que passou, commit, arquivo).
- **Em andamento** — o que está a meio caminho, e onde exatamente parou.
- **Decidido** — decisão tomada hoje que ainda não virou registro na fonte. É
  daqui que o `/dds:End` promove.
- **Aberto** — o que apareceu e não foi resolvido.

Se o usuário passou uma nota como argumento, ela entra em **Em andamento**.

Não regenere o cérebro e não commite — isto é checkpoint, e o dia ainda não
fechou. Ao terminar, diga em uma linha o que foi gravado e onde.
