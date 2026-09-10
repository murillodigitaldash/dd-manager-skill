# DDS — protocolo do cérebro

Plugin do Claude Code que dá a qualquer projeto o mesmo protocolo diário:
retrospecto por evidência, fila de execução, e promoção do que aconteceu hoje
para a documentação-fonte.

## Instalar

```
/plugin marketplace add murillodigitaldash/dd-manager-skill
/plugin install dds
```

## Usar

| Comando | O que faz |
|---|---|
| `/dds:Build` | constrói o cérebro do projeto quando ele ainda não existe |
| `/dds:Start` | abre a sessão — retrospecto da última e fila de hoje |
| `/dds:Status` | fila e situação das fases, sem retrospecto |
| `/dds:Next` | pega o topo da fila e entra nele |
| `/dds:Save` | checkpoint do diário no meio da sessão |
| `/dds:End` | fecha o dia: diário, promoção, regeneração e commit |

## O contrato

Cada projeto declara o seu em `.claude/dd.md`:

```yaml
---
vault: cerebro
gerador: python3 ferramentas/gerar_cerebro.py
---
```

As zonas do vault, o mapa da fonte e os pré-requisitos não se declaram aqui:
vêm do próprio gerador, que responde `--contrato` em JSON. Uma fonte só para
cada fato.

## Desenvolver

```
python3 -m unittest discover -s tests -v
```
