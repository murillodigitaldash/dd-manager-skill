# DDS — protocolo do cérebro

Plugin do Claude Code que dá a qualquer projeto o mesmo protocolo diário:
retrospecto por evidência, fila de execução, e promoção do que aconteceu hoje
para a documentação-fonte.

## A ideia em um parágrafo

O **cérebro** é um vault Obsidian gerado a partir da documentação do
repositório. Ele não é a fonte — é o espelho dela. Conhecimento novo se
escreve na fonte e se regenera; o vault existe para ser navegado, ligado e
lido, não editado. Toda a plugin é a consequência dessa única regra: onde
escrever, o que nunca sobrescrever, e o que conferir antes de apagar.

Nada aqui é caminho fixo. Onde o vault fica, quem o gera e onde mora cada
tipo de documento vêm do **contrato** que cada projeto declara — a plugin roda
igual num monorepo e num repositório de uma pasta só.

## Instalar

```
/plugin marketplace add murillodigitaldash/dd-manager-skill
/plugin install dds@dd-manager
```

Pré-requisito: `python3` no `PATH` — todo script da plugin roda nele, sem
dependência externa. O projeto precisa ser um repositório git: a proteção
contra perda de nota é feita de `git status`, e fora de um repositório ela
passaria sem conferir nada.

## Os comandos

| Comando | O que faz |
|---|---|
| `/dds:Build` | constrói o cérebro do projeto quando ele ainda não existe |
| `/dds:Start` | abre a sessão — retrospecto da última e fila de hoje |
| `/dds:Status` | fila e situação das fases, sem retrospecto |
| `/dds:Next` | pega o topo da fila e entra nele |
| `/dds:Save` | checkpoint do diário no meio da sessão |
| `/dds:End` | fecha o dia: diário, promoção, regeneração e commit |

Os três primeiros só leem. `Save` e `End` escrevem, e `End` é o único que
regenera o vault.

## Passo a passo — o dia 1, com `/dds:Build`

`/dds:Build` é o único comando que constrói. Ele nunca reconstrói por cima de
um cérebro que já existe: a zona semeada guarda respostas que só existem ali.

1. **Decidir o caso.** Lê o contrato. Se já há contrato e o vault está
   completo, o comando diz quantas notas existem e encerra — regenerar é
   trabalho do `/dds:End`, que faz isso com proteção.

2. **Entrevistar**, quando ainda não há contrato. Quatro perguntas: onde está
   a documentação-fonte, onde o vault deve nascer, que documento é
   pré-requisito, e como se chama a zona espelhada dentro do vault.

   Um projeto que chega sem documentação nenhuma responde mais quatro
   perguntas sobre o projeto em si — do que se trata, o que já existe, o que
   está em aberto — e essas respostas viram o primeiro documento da fonte.

3. **Semear a fonte.** Nos dois casos — com documentação prévia ou sem ela —
   a pasta-fonte recebe os arquivos que o protocolo lê: a visão geral, o
   backlog (de onde sai a fila) e o índice de decisões arquiteturais. Eles
   nascem com **estrutura e sem conteúdo fabricado**.

   A semeadura nunca sobrescreve. Cada arquivo recebe um de três vereditos:

   | Veredito | O que aconteceu |
   |---|---|
   | `criado` | não existia; nasceu com a estrutura que o protocolo lê |
   | `preservado` | já existia, com a estrutura certa — não foi tocado |
   | `estrutura_incompleta` | já existia sem a estrutura; **não foi consertado**, só reportado |

   O terceiro caso é aviso, não erro. Consertar seria reescrever um arquivo
   do usuário, que é exatamente o que essa etapa existe para não fazer.

4. **Escrever as duas peças.** O gerador, copiado de um esqueleto e com as
   respostas da entrevista preenchidas; e o contrato, em `.claude/dd.md`. O
   comando então confere campo a campo o que o contrato devolveu contra o que
   a entrevista pediu — um gerador que "funciona por coincidência", porque as
   respostas calharam de bater com os padrões do esqueleto, é pego aqui.

5. **Gerar, verificar e commitar.** A geração passa sempre pela guarda. A
   verificação acusa link quebrado e nota vazia como erro, e nome ambíguo
   como aviso.

## Passo a passo — o dia a dia

```
/dds:Start  →  /dds:Next  →  (trabalho)  →  /dds:Save  →  /dds:End
```

- **`/dds:Start`** monta o retrospecto da última sessão a partir de evidência
  — commits, diário, ledger —, não de memória, e apresenta a fila de hoje.
- **`/dds:Next`** pega o topo da fila e entra nele, roteando para a skill
  certa conforme o item seja um plano a executar, uma ideia a desenhar ou um
  defeito a investigar.
- **`/dds:Save`** grava um checkpoint no diário no meio da sessão, para que um
  contexto perdido não leve o dia junto.
- **`/dds:End`** fecha o dia em quatro tempos: escreve o diário, **promove**
  para a fonte o que aconteceu (item entregue vai para o backlog, decisão vira
  ADR, questão respondida é marcada), regenera o vault pela guarda e commita.

## Como funciona por dentro

### As três zonas do vault

Toda a segurança da plugin sai daqui. O gerador declara três zonas, e cada
uma tem uma regra de escrita diferente:

| Zona | Regra | Para que serve |
|---|---|---|
| **reescrita** | apagada e reescrita a cada geração | o espelho da fonte |
| **semeada** | criada uma vez, nunca sobrescrita | respostas que a fonte não tem |
| **livre** | o gerador nunca entra | anotação pessoal, rascunho |

Escrever na zona reescrita é perder o texto na próxima geração. Para gravar
conhecimento novo: escreva na fonte e regenere.

### O contrato

Cada projeto declara o seu em `.claude/dd.md`:

```yaml
---
vault: cerebro
gerador: python3 ferramentas/gerar_cerebro.py
---
```

Só isso. As zonas, o mapa da fonte e os pré-requisitos **não** se declaram
aqui: vêm do próprio gerador, que responde `--contrato` em JSON. Uma fonte só
para cada fato — declarar nos dois lugares criaria duas verdades, e duas
verdades divergem.

Trocar o gerador por outro, com ontologia própria e notas derivadas, não
quebra nada: o que a plugin exige é a interface (`--contrato` e as três
zonas), não a implementação.

### A fila de execução

Não existe um arquivo "fila". Ela se lê cruzando quatro fontes, nesta ordem
de precedência:

1. O que a seção `### Execução` da fase corrente já registra como entregue.
2. A tabela de itens da mesma fase — o que não aparece como entregue está
   aberto.
3. Planos escritos sem ledger de execução correspondente — plano escrito e
   não executado é o topo da fila.
4. Questões em aberto que bloqueiam algum item.

### A guarda da regeneração

Regenerar apaga uma pasta inteira e a reescreve. Por isso o gerador nunca é
chamado direto — a chamada passa por uma guarda que põe duas travas:

- **antes**: recusa se houver edição não commitada em zona reescrita, porque
  regenerar apagaria esse trabalho;
- **depois**: se a geração apagou alguma nota, restaura o vault do git e para,
  nomeando o que sumiu.

Nota que some tem duas causas, e a guarda nomeia as duas: **fonte incompleta**
(devolva o conteúdo à fonte e rode de novo) ou **documento removido de
propósito** (devolvê-lo desfaria a remoção; commite a remoção e rode de novo).

### Os scripts

| Script | Papel |
|---|---|
| `contrato.py` | resolve o contrato do projeto e o devolve em JSON |
| `semeador.py` | semeia a pasta-fonte; nunca sobrescreve |
| `guarda.py` | envelopa a geração com as duas travas |
| `esqueleto_gerador.py` | ponto de partida do gerador, copiado para o projeto |

Os três primeiros são da plugin e rodam de dentro dela. O quarto é o único
que vira arquivo do projeto — e é seu para reescrever.

## `superpowers`

Recomendada, não obrigatória. Quando instalada, dois pontos da DDS a usam:

- `/dds:Next` roteia para `superpowers:subagent-driven-development`,
  `superpowers:brainstorming`, `superpowers:writing-plans` ou
  `superpowers:systematic-debugging`, conforme o item da fila.
- O ledger de execução é escrito por `subagent-driven-development` ao executar
  um plano — nenhum comando `dds` o produz.

Sem `superpowers`, `/dds:Next` apresenta o item e devolve a decisão ao
usuário em vez de invocar uma skill inexistente, e a fila deixa de distinguir
plano executado de plano só escrito, porque nada grava o ledger.

## Convenções

- Tudo em português: notas, mensagens de commit, comentários.
- Data absoluta, nunca relativa.
- Mensagem de commit do cérebro: `docs(cerebro): <o que mudou>`.

## Desenvolver

```
python3 -m unittest discover -s tests -v
```

A suíte é o portão de regressão da plugin, e uma parte dela existe para uma
coisa só: garantir que nada aqui dependa de um projeto específico. Ela varre
o que viaja para a máquina de quem instala e reprova caminho absoluto,
invocação de script por caminho relativo e documento citado pelo nome —
pela **forma** do defeito, sem precisar saber nome de projeto nenhum.
