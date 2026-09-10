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
| há contrato, o vault existe, mas falta zona semeada | **construir** — o passo 3 semeia o que falta. Leia o passo 5 antes |
| há contrato e o vault está completo | **não construa.** Diga quantas notas tem e que regenerar é `/dds:End`, que já faz isso com guarda. Encerre aqui |

O último caso não é falha do comando: é o comando fazendo o seu trabalho.

Conte as notas com o `vault` do contrato:

```sh
find "<vault>" -name '*.md' -not -path '*/.obsidian/*' | wc -l
```

### 2. Entrevistar, quando não há contrato

Quatro perguntas, e só elas. Use `AskUserQuestion` quando houver alternativa
real; pergunte em texto quando a resposta for um caminho.

1. **Onde está a documentação-fonte?** Uma pasta de Markdown. Se o projeto não
   tiver nenhuma, **pare aqui**: espelho sem objeto não reflete nada, e o
   conserto é escrever documentação, não gerar um vault vazio.
2. **Onde o vault deve nascer?** Padrão `cerebro/`.
3. **Que documento é pré-requisito?** Sem ele, gerar produziria um cérebro que
   *parece* completo. Pode ser a própria pasta do item 1.
4. **Como se chama a pasta espelhada dentro do vault?** Padrão
   `10 Documentos`.

Então escreva as duas peças:

**O gerador**, copiado do esqueleto e com as quatro constantes preenchidas:

```sh
mkdir -p ferramentas
cp "$CLAUDE_PLUGIN_ROOT/skills/dds/scripts/esqueleto_gerador.py" \
   ferramentas/gerar_cerebro.py
```

Edite o bloco `# ── configuração ──` com as respostas. Não toque no resto: a
DDS depende de `--contrato`, e a guarda depende das três zonas.

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

### 3. Conferir a fonte e gerar

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
python3 <gerador> --verificar
```

Aviso não interrompe a construção — é relatado ao usuário, e a construção segue.
Só o erro (código de saída diferente de zero) faz o comando parar.

Confirme também que as pastas de `zonas.semeada` e `zonas.livre` existem — são
as que fazem o vault ser do usuário, e não do gerador.

### 5. Nunca use `--semear` num vault que já existe

`--semear` **sobrescreve** a zona semeada: as pastas onde moram respostas que a
fonte não tem. Sobrescrever é perdê-las, e elas não voltam pela regeneração,
porque a fonte nunca as teve.

Só há um caso legítimo: a pasta semeada **não existe**. Aí ela nasce sozinha na
geração normal do passo 3, sem `--semear`.

Se o vault parecer errado e a tentação for semear de novo, pare: o conserto de
nota que sumiu é **devolvê-la à fonte**, nunca recriar o vault por cima.

### 6. Commitar

```
docs(cerebro): construir o cerebro a partir da fonte

<corpo: quantas notas, e o que a fonte tinha que permitiu gera-las>
```

Inclua o vault, `.claude/dd.md` e o gerador, se a entrevista os criou.

### 7. Devolver o resumo

Nesta forma, sem preâmbulo e sem fechamento:

## Situação encontrada
Uma linha: qual dos quatro casos do passo 1, e por quê.

## Construído
Contagem por zona — reescritas, semeadas, preservadas — e o total. Se nada foi
construído porque o cérebro já existia, um bullet dizendo isso.

## Verificação
O que o `--verificar` respondeu, em uma linha.

## Commit
Hash curto e primeira linha da mensagem. Se não houve, diga que não houve.

## Como abrir
Caminho para `Open folder as vault` no Obsidian.
