---
description: Constrói o cérebro do projeto quando ele ainda não existe — entrevista se falta contrato, confere a fonte, gera, verifica e commita.
---

Carregue o protocolo com a skill `dds`.

O cérebro é **espelho da fonte**, e este comando existe para o caso em que o
espelho ainda não foi montado. Ele nunca reconstrói por cima de um cérebro que
já existe: a zona semeada guarda respostas que só existem ali, e reconstruir
sem cuidado é apagá-las.

Execute na ordem. Se um passo falhar, **pare e reporte** — não pule para o
seguinte.

### 1. Decidir o caso

```sh
python3 "$CLAUDE_PLUGIN_ROOT/skills/dds/scripts/contrato.py"
```

| Situação | O que fazer |
|---|---|
| não há `.claude/dd.md` | **entrevistar** — passo 2, e depois o 3 |
| há contrato, e o vault não existe ou tem zero nota | **construir** — passo 3 |
| há contrato, o vault existe, mas falta alguma pasta de `zonas.semeada` ou `zonas.livre` | **construir** — o passo 3 semeia o que falta. Leia o passo 5 antes |
| há contrato e o vault está completo | **não construa.** Diga quantas notas tem e que regenerar é `/dds:End`, que já faz isso com guarda. Encerre aqui |

O último caso não é falha do comando: é o comando fazendo o seu trabalho.

Conte as notas com o `vault` do contrato:

```sh
find "<vault>" -name '*.md' -not -path '*/.obsidian/*' | wc -l
```

### 2. Entrevistar, quando não há contrato

Quatro perguntas no caminho normal. Use `AskUserQuestion` quando houver
alternativa real; pergunte em texto quando a resposta for um caminho ou uma
resposta aberta.

1. **Onde está a documentação-fonte?** Uma pasta de Markdown.

   Se o projeto já tem alguma, essa pasta é `FONTE`.

   Se **não tiver nenhuma**, o comando não para mais aqui. Confirme com o
   usuário, em texto, a pasta onde a documentação vai passar a morar — padrão
   `docs/` — e essa pasta confirmada também é `FONTE`. Antes de seguir
   adiante, semeie essa fonte: quatro perguntas sobre o **projeto**, não
   sobre caminhos, no mesmo turno — e como são respostas abertas, pergunte em
   texto, e não com `AskUserQuestion`:

   a. Como se chama o projeto (ou este documento), numa frase curta? Vira o
      título do documento — sem essa pergunta, nada nas outras três dá nome
      a coisa nenhuma.
   b. Do que se trata o projeto, e que problema ele resolve?
   c. O que já está decidido ou já existe?
   d. O que ainda está em aberto?

   <!--
     O documento desta semeadura nasce dentro de FONTE — a pasta-fonte que
     acabou de ser confirmada — e NUNCA dentro do vault. Isto não é estilo,
     é a regra que organiza a plugin inteira: a zona reescrita é apagada e
     reescrita a cada geração, e um documento escrito ali não existe na
     fonte para ser recriado — a próxima geração o apaga sem avisar. Se este
     comentário for removido por parecer "simplificação", o próximo
     /dds:Build ou /dds:End apaga o trabalho de quem escreveu aqui.
   -->

   Monte o corpo de **um** documento Markdown com as respostas — o conteúdo
   é do usuário, nunca invente no lugar dele. Se ele não responder uma das
   quatro, a seção (ou o título, no caso da pergunta a) correspondente fica
   só com a linha "Em aberto — ainda não respondido.":

   ```markdown
   # <resposta a, ou "Em aberto — ainda não respondido.">

   ## Do que se trata

   <resposta b, ou "Em aberto — ainda não respondido.">

   ## O que já existe

   <resposta c, ou "Em aberto — ainda não respondido.">

   ## O que está em aberto

   <resposta d, ou "Em aberto — ainda não respondido.">

   ## Próximos passos

   Continue escrevendo aqui, na fonte, e regenere — nunca no vault: a zona
   reescrita é apagada e reescrita a cada geração.
   ```

   **Não escreva o arquivo você mesmo.** Passe o corpo ao semeador — é ele
   que decide escrever ou preservar, e essa decisão é código, não instrução:

   ```sh
   python3 "$CLAUDE_PLUGIN_ROOT/skills/dds/scripts/semeador.py" \
     --fonte "<FONTE>" --visao-geral - <<'MD'
   <o corpo montado acima>
   MD
   ```

   **Se o projeto já tinha documentação** — o outro ramo desta pergunta —
   não houve entrevista e não há corpo a passar. Rode a mesma chamada sem
   `--visao-geral`:

   ```sh
   python3 "$CLAUDE_PLUGIN_ROOT/skills/dds/scripts/semeador.py" --fonte "<FONTE>"
   ```

   **Os dois ramos convergem aqui**, e é por isso que a chamada aparece nos
   dois: `backlog.md` e `adrs/indice.md` são semeados sempre, com
   documentação prévia ou sem ela. São os destinos que `fonte.backlog` e
   `fonte.indice_adrs` declaram desde já no gerador (passo seguinte); sem
   eles, o primeiro `/dds:Status` de **qualquer** projeto encontra backlog
   ilegível, e a primeira promoção do `/dds:End` não tem onde escrever.

   O que o semeador garante — e por isso você não precisa garantir:

   - **Nunca sobrescreve.** É a mesma arma carregada que o `--semear` do
     gerador existe para travar (passo 5): o que é do usuário não se recria
     por cima, e ele pode já ter `backlog.md` ou `adrs/indice.md` de um
     histórico próprio.
   - **Os três arquivos nascem dentro de `FONTE`**, nunca no vault — a zona
     reescrita é apagada e reescrita a cada geração.
   - **Não conserta arquivo alheio.** Um arquivo que existe sem a estrutura
     que o protocolo lê vira aviso, não conserto silencioso.

   Ele devolve JSON, um veredito por arquivo:

   ```json
   {"arquivos": [{"caminho": "docs/visao-geral.md", "veredito": "criado"},
                 {"caminho": "docs/backlog.md", "veredito": "estrutura_incompleta",
                  "falta": ["a seção `### Execução`, de onde sai a fila de execução"]},
                 {"caminho": "docs/adrs/indice.md", "veredito": "preservado"}]}
   ```

   Relate ao usuário uma linha por arquivo, com o veredito que **veio** — não
   o que você esperava que viesse — e guarde este JSON para o passo 7. Em
   `estrutura_incompleta`, nomeie o que `falta` e siga: é aviso, não erro, e
   a decisão é de quem escreveu o arquivo.

   Se o script sair 1, **pare e reporte**: ou a pasta-fonte não existe (a
   resposta da pergunta 1 está errada), ou o corpo chegou vazio no stdin.
   Nos dois casos ele não escreveu nada.

   Só então siga para a pergunta 2 — os dois ramos acima convergem aqui.

2. **Onde o vault deve nascer?** Padrão `cerebro/`.
3. **Que documento nomeado é pré-requisito?** Não a pasta do item 1 inteira —
   um arquivo específico, sem o qual o cérebro enganaria: pareceria completo
   sem ser. Se genuinamente não houver nenhum documento assim, a resposta é
   **"nenhum"**, dita explicitamente — não a pasta do item 1 repetida, que
   responde sem decidir nada. O custo de cada escolha: nomear um documento
   faz o passo 3 recusar gerar enquanto ele não existir; responder "nenhum"
   abre mão dessa checagem, e uma fonte incompleta vai gerar um vault que
   *parece* completo, sem que nada avise.
4. **Como se chama a zona reescrita dentro do vault?** Padrão
   `10 Documentos`.

Depois de saber onde mora a fonte (item 1), confira se os caminhos padrão de
`artefatos` (`docs/superpowers/execucao`, `docs/superpowers/plans`,
`docs/superpowers/specs`) caem dentro dela — caso comum quando a resposta do
item 1 é `docs/`. Se caírem, diga isso ao usuário numa linha e ofereça as duas
saídas: aceitar que diário e planos virem notas do vault também, ou declarar
`diario`, `planos` e `specs` no frontmatter do contrato, apontando para fora
da fonte.

Então escreva as duas peças:

**O gerador**, copiado do esqueleto e com as quatro constantes da entrevista
preenchidas:

```sh
mkdir -p ferramentas
cp "$CLAUDE_PLUGIN_ROOT/skills/dds/scripts/esqueleto_gerador.py" \
   ferramentas/gerar_cerebro.py
```

Edite o bloco `# ── configuração ──` com as respostas. As três constantes
seguintes (`BACKLOG`, `ADRS`, `INDICE_ADRS`) já nascem certas, derivadas de
`FONTE` — só as edite se este projeto guardar backlog ou ADRs num lugar
diferente. Não toque no resto do arquivo: a DDS depende de `--contrato`, e a
guarda depende das três zonas.

**O contrato**, em `.claude/dd.md`:

```markdown
---
vault: <resposta 2>
gerador: python3 ferramentas/gerar_cerebro.py
---

# O cérebro deste projeto

<duas ou três frases: o que este projeto espelha, o que cada zona guarda, e o
que um humano precisa saber antes de escrever no vault>
```

Confirme que o contrato resolve antes de seguir:

```sh
python3 "$CLAUDE_PLUGIN_ROOT/skills/dds/scripts/contrato.py"
```

Se `origem_zonas` vier `"escape"`, algo está errado com o gerador recém-escrito
— investigue em vez de aceitar.

Isso não basta. Quando as respostas da entrevista coincidem com os padrões do
esqueleto, o bloco `# ── configuração ──` pode nunca ter sido editado de fato
e o contrato resolve assim mesmo, por coincidência. Se as respostas
divergirem dos padrões e a edição for esquecida, o erro só aparece muito
depois, como espelho vazio — e uma conferência que só olha `origem_zonas` não
pega este caso, porque `origem_zonas` só denuncia gerador que não responde
`--contrato`, não gerador que responde errado.

Compare, campo a campo, o que o contrato devolveu contra as respostas desta
entrevista:

| Campo do contrato | Tem que bater com |
|---|---|
| `fonte.documentos` | `FONTE` — resposta 1 (ou a pasta confirmada na semeadura) |
| `vault` (raiz do JSON) | `VAULT` — resposta 2, o mesmo valor escrito em `.claude/dd.md` |
| `fonte.questoes`, antes de `/70 Decisões em aberto` | `VAULT` — resposta 2 de novo, mas vazando do gerador, não do frontmatter |
| `zonas.reescrita[0]` | `ZONA_ESPELHO` — resposta 4. `ZONA_ESPELHO` é só o nome da constante no gerador; a zona em si se chama `zonas.reescrita` |
| `prerequisitos` | `PREREQUISITOS` — resposta 3: a lista com o documento nomeado, ou lista vazia se a resposta foi "nenhum" — **nunca** a pasta do item 1, mesmo que o esqueleto tenha vindo assim |
| `fonte.backlog`, `fonte.adrs`, `fonte.indice_adrs` | dentro de `FONTE` — resposta 1: os três derivam dela e não pedem resposta própria; se um deles não fizer sentido para este projeto, remova a chave do `CONTRATO` em vez de inventar destino |

As duas linhas de `VAULT` conferem coisas diferentes: `vault` vem do
`.claude/dd.md` que você acabou de escrever, e `fonte.questoes` vaza do
`VAULT` de dentro do gerador. Se uma bater e a outra não, o defeito está
localizado — um dos dois arquivos ficou com o valor errado.

A linha de `prerequisitos` merece atenção à parte: o esqueleto vem com
`PREREQUISITOS = ["docs"]` por padrão — a própria pasta do item 1. Se a
pergunta 3 recebeu um documento nomeado, ou "nenhum" como resposta
explícita, e ninguém editar essa constante, o contrato continua devolvendo
`["docs"]`: a pasta existe, o passo 3 passa, e a resposta do usuário foi
descartada em silêncio — exatamente o "funciona por coincidência" que esta
conferência existe para pegar, e exatamente o "responde sem decidir nada"
que a pergunta 3 foi reescrita para evitar.

Se algum campo divergir, **pare** e nomeie o campo e a divergência: o valor
que o contrato devolveu contra o que a entrevista pediu.

### 3. Conferir a fonte e gerar

Antes de tudo, confirme que há repositório git:

```sh
git rev-parse --git-dir
```

Se falhar, **pare** e diga ao usuário para inicializar o git antes de
construir — não gere nada. As duas guardas de `guarda.py` leem `git status`
para decidir se recusam; fora de um repositório, `git status` volta vazio, as
duas guardas passam sem conferir nada, e o problema só apareceria no commit
do passo 6, tarde demais para evitar uma geração sem rede de segurança.

Confira que **cada** caminho de `prerequisitos` existe. Se algum faltar, pare.
Diga o que falta e não gere nada: sem fonte, não há o que espelhar, e um cérebro
pela metade é pior que nenhum — ele parece completo.

Depois, sempre pela guarda:

```sh
python3 "$CLAUDE_PLUGIN_ROOT/skills/dds/scripts/guarda.py"
```

Nunca chame o gerador direto — vale igual na primeira construção.

Se a guarda recusar por edição não commitada em zona reescrita, a causa provável
aqui é remoção em *staged* (alguém rodou `git rm` no vault). Commite a remoção
e rode de novo; não contorne a guarda.

### 4. Verificar o que nasceu

```sh
<gerador> --verificar
```

Aviso não interrompe a construção — é relatado ao usuário, e a construção segue.
Só o erro (código de saída diferente de zero) faz o comando parar.

Se der erro aqui, o vault **já foi gerado** pelo passo 3 e ainda não foi
commitado — pare, mas não deixe o projeto nesse estado sem dizer o que fazer.
Duas saídas, e a decisão é do usuário: corrigir a fonte e rodar a guarda de
novo (passo 3), ou commitar o que já nasceu e corrigir depois. O que não vale
é parar calado: um vault gerado e não commitado não é pendência visível para
ninguém — o passo 1 deste mesmo comando decide pela existência de notas e
pastas, não por commit, e uma próxima execução leria esse vault como
completo e diria para não construir, escondendo o erro de verificação que
nunca foi corrigido. Enquanto isso, o conteúdo inteiro nunca chegou a ser
commitado — está a um `git clean` de sumir sem deixar rastro.

Confirme também que as pastas de `zonas.semeada` e `zonas.livre` existem — são
as que fazem o vault ser do usuário, e não do gerador.

### 5. Nunca use `--semear` num vault que já existe

`--semear` **recusa e sai 1** quando a zona semeada já existe — ela não
sobrescreve nada. A proteção existe porque a zona semeada guarda respostas que
a fonte não tem: se `--semear` sobrescrevesse, perdê-las seria o efeito
colateral de um comando que parece inofensivo.

Só há um caso legítimo para chamar `--semear`: a pasta semeada **não existe**.
Aí ela nasce sozinha na geração normal do passo 3, sem precisar de `--semear`
à parte.

Se o vault parecer errado e a tentação for semear de novo, pare: o conserto de
nota que sumiu é **devolvê-la à fonte**, nunca recriar o vault por cima.

### 6. Commitar

```
docs(cerebro): construir o cerebro a partir da fonte

<corpo: quantas notas, e o que a fonte tinha que permitiu gera-las>
```

Inclua o vault, `.claude/dd.md`, o gerador, e os arquivos que o semeador
reportou como **`criado`** no passo 2 — `visao-geral.md`, `backlog.md` e
`adrs/indice.md`. Um arquivo **`preservado`** ou **`estrutura_incompleta`**
já era do projeto antes desta execução: não é coisa deste commit.

### 7. Devolver o resumo

Nesta forma, sem preâmbulo e sem fechamento:

## Situação encontrada
Uma linha: qual dos quatro casos do passo 1, e por quê.

## Construído
Contagem por zona. Para cada nome em `zonas.reescrita`, `zonas.semeada` e
`zonas.livre` do contrato, some as notas com:

```sh
find "<vault>/<zona>" -name '*.md' -not -path '*/.obsidian/*' | wc -l
```

Reporte os três totais (reescrita, semeada, livre) e a soma dos três. Se nada
foi construído porque o cérebro já existia, um bullet dizendo isso.

## O que foi semeado
Só se o passo 2 chamou o semeador. Um bullet por arquivo do JSON que ele
devolveu, e cada bullet **declara o veredito que veio** — `criado`,
`preservado` ou `estrutura_incompleta` — nunca uma frase que sirva igual
para mais de um, porque anunciar como criado o que só foi preservado é
falso. O JSON é a fonte desta seção; não reconstrua de memória o que foi
qual:

- `visao-geral.md`, **criado** — o retrato inicial do projeto; edite
  direto, na fonte. *Ou* **preservado** — já existia, não foi tocado.
- `backlog.md`, **criado** — nasceu com a estrutura vazia; a fila de
  execução sai daqui: abra uma seção de fase, some itens à tabela, feche o
  que foi entregue em `### Execução`. *Ou* **preservado** — já existia, com
  a estrutura que o protocolo lê. *Ou* **estrutura_incompleta** — existe e
  não foi tocado, mas falta o que o `falta` do JSON nomeia, e até isso ser
  resolvido a fila não é legível.
- `adrs/indice.md`, mesmos três vereditos, mesma regra. Toda decisão
  arquitetural vira um arquivo novo em `adrs/`, listado e contado aqui.

Se a zona semeada de questões (`70 Decisões em aberto`, no vault) nasceu
nesta execução, mais um bullet: questão em aberto mora ali, e se edita
direto, sem passar pela fonte.

Se nada foi criado nem preservado nesta execução, pule esta seção.

## Verificação
O que o `--verificar` respondeu, em uma linha.

## Commit
Hash curto e primeira linha da mensagem. Se não houve, diga que não houve.

## Como abrir
Caminho para `Open folder as vault` no Obsidian.
