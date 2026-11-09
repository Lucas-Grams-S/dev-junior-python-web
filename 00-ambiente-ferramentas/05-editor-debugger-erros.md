# 05. VS Code, debugger, ler erros, pesquisar e pedir ajuda

> ⏱️ ~1h30 · Módulo 0 · Pré-requisitos: [02](02-python-venv-uv.md), [03](03-git-local.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Configurar o VS Code com o interpretador da `.venv` e o Ruff
- Depurar um programa com breakpoints, inspecionando variáveis
- Ler um *traceback* de baixo para cima e achar a linha do problema
- Montar uma pergunta de ajuda que alguém consiga responder
- Usar IA como apoio sem terceirizar o aprendizado

## 🤔 Por que isso importa
Um dev júnior passa boa parte do tempo lendo erro e código dos outros. Quem lê o erro direito resolve em minutos o que levaria horas. E quem usa IA sem entender entrega código que não sabe defender, o que aparece rápido em code review e entrevista.

## 💡 Intuição (explicação simples)
- **Debugger** = pausar um filme no meio e olhar cada objeto da cena, em vez de tentar adivinhar o que aconteceu assistindo de novo.
- **Traceback** = o rastro de pegadas até a cena do problema: a pegada mais recente (última linha) é onde caiu; as de cima mostram como chegou lá.
- **Pedir ajuda** = chamar o mecânico dizendo o sintoma, quando começou e o que já tentou, não só “o carro não anda”.

## 🔬 Como funciona por dentro
**Traceback.** O Python imprime a pilha de chamadas (da mais antiga para a mais recente) e termina com **o tipo e a mensagem da exceção**. Leia **de baixo para cima**: 1º a última linha (o quê), 2º a última linha do *seu* código (onde).

**Debugger.** Ao chegar num *breakpoint*, o interpretador pausa e entrega o controle: você vê as variáveis e executa linha a linha.

| Ação | Atalho no VS Code | Faz |
|---|---|---|
| Continuar | `F5` | Roda até o próximo breakpoint |
| Passo sobre | `F10` | Executa a linha sem entrar em funções |
| Passo para dentro | `F11` | Entra na função chamada |
| Sair | `Shift+F11` | Termina a função atual |

**Alternativa sem editor:** `breakpoint()` no código abre o `pdb` no terminal (comandos: `n` próxima linha, `s` entrar, `c` continuar, `p var` imprimir, `q` sair). Documentação: [pdb](https://docs.python.org/3/library/pdb.html).

## 🛠️ Exemplo prático
**1. Configurar o VS Code.** Abra a pasta do projeto (`code .`). Instale as extensões **Python** e **Ruff** (da Microsoft e da Astral). Com um `.py` aberto, `Ctrl+Shift+P` → *Python: Select Interpreter* → escolha o `./.venv/bin/python`. Se a `.venv` não aparecer, rode `uv sync` e recarregue a janela. Referência: [Python debugging in VS Code](https://code.visualstudio.com/docs/python/debugging). ⚠️ Os passos da interface não foram executados pelo autor; confira os nomes dos menus na sua versão.

**2. Ler um erro.** Crie `bug.py`:
```python
def media(notas):
    return sum(notas) / len(notas)

print(media([7, 8]))
print(media([]))
```
```bash
uv run bug.py
```
Saída (caminhos encurtados):
```text
7.5
Traceback (most recent call last):
  File "bug.py", line 5, in <module>
    print(media([]))
          ~~~~~^^^^
  File "bug.py", line 2, in media
    return sum(notas) / len(notas)
           ~~~~~~~~~~~^~~~~~~~~~~
ZeroDivisionError: division by zero
```
Leitura: (1) tipo e mensagem: `ZeroDivisionError: division by zero`; (2) onde: linha 2, dentro de `media`; (3) quem chamou: linha 5. Os `~~~^^^` marcam a parte exata da expressão que falhou. Causa: `len([])` é `0`.

**3. Depurar.** Clique à esquerda do número da linha 2 (bolinha vermelha) e aperte `F5` → *Python Debugger: Current File*. O programa para antes da linha 2: o painel *Variables* mostra `notas = [7, 8]`; `F5` de novo e na segunda chamada você verá `notas = []`. Sem editor, o equivalente:
```python
def media(notas):
    breakpoint()          # abre o pdb aqui
    return sum(notas) / len(notas)
```
Apague o `breakpoint()` antes de commitar.

**4. Uma boa pergunta de ajuda** (para colega, fórum ou IA):
```text
Título: ZeroDivisionError ao calcular média de lista vazia (Python 3.13)

O que quero: calcular a média das notas de um produto.
O que acontece: [traceback completo, em texto]
Código mínimo que reproduz: [10 linhas, não o projeto inteiro]
O que já tentei: li a doc de sum(); conferi que a lista vem vazia.
Ambiente: Ubuntu 24.04 (WSL), Python 3.13, uv 0.13.
```

## 🧠 Pausa para lógica
**Problema.** A função `media` quebra com lista vazia. Qual deve ser o comportamento correto? Escreva duas versões.

<details><summary>Dica</summary>
Existem duas filosofias: tratar o caso vazio devolvendo um valor neutro, ou considerar que isso é um erro de quem chamou e avisar com uma exceção clara.
</details>

<details><summary>Solução comentada</summary>

```python
def media_ou_none(notas):
    if not notas:            # lista vazia é "falsa" em Python
        return None          # o chamador precisa tratar None
    return sum(notas) / len(notas)

def media_estrita(notas):
    if not notas:
        raise ValueError("notas não pode ser vazia")   # erro explícito e com mensagem útil
    return sum(notas) / len(notas)
```
Não há resposta única: devolver `None` é prático quando “sem notas” é normal (um produto novo); levantar exceção é melhor quando vazio indica bug. O importante é **decidir e documentar**. Nunca devolver `0`, pois confunde “média zero” com “sem dados”.
</details>

**Variação mais difícil:** na versão com `None`, o que acontece com `media_ou_none([]) + 1`? Qual mensagem o Python mostra?

## ⚠️ Erros comuns e boas práticas
- **Ler só a primeira linha do erro**, ou colar só o final. Sempre copie o traceback inteiro.
- **Mexer em várias coisas ao mesmo tempo.** Mude uma, teste, repita.
- **`print` por toda parte** até virar bagunça: aprenda o breakpoint; use `print` só para olhadas rápidas e remova antes do commit.
- **Pesquisar a mensagem de erro**: remova partes do seu projeto (caminhos, nomes) e pesquise o tipo + mensagem, em inglês (`ZeroDivisionError python`). Prefira, nesta ordem: documentação oficial, Stack Overflow com resposta aceita e recente, blogs.
- Mensagens frequentes que já viu: `ModuleNotFoundError` (aula 02), `Permission denied` (aula 01), `Author identity unknown` (aula 03).

### Uso responsável de IA (assistente de código)
| Faça | Evite |
|---|---|
| Cole o traceback e peça para **explicar** o erro | Colar o enunciado do exercício e copiar a resposta |
| Tente primeiro; peça revisão do que escreveu | Aceitar código que você não sabe explicar linha a linha |
| Peça um exemplo menor de um conceito | Enviar segredos, chaves, dados de clientes ou código confidencial da empresa |
| Verifique em documentação e **rode** o que ela sugeriu | Confiar em nomes de funções/pacotes: IA inventa APIs que não existem |

Regra do curso: se você não consegue explicar o código em voz alta, ele não está “pronto”, ainda que funcione.

## 🧩 Exercícios
**1. Fixação**
Qual é o tipo do erro, em que linha dele (do seu código) e quem o chamou?
```text
Traceback (most recent call last):
  File "loja.py", line 9, in <module>
    total = somar(["10", 5])
  File "loja.py", line 3, in somar
    return a + b
TypeError: can only concatenate str (not "int") to str
```
<details><summary>Solução</summary>

Tipo: `TypeError` (somar `str` com `int`). Falha na linha 3, em `somar` (`a + b`), chamada na linha 9 com `"10"` (texto) e `5` (número). A correção é converter na entrada: `int("10") + 5`, ou validar os dados antes.
</details>

**2. Aplicação no projeto MiniShop**
No seu `main.py`, crie uma função `price_with_tax(price, rate)` com um bug proposital (divisão por zero ou tipo errado), depure-a e corrija.

Critérios de pronto:
- [ ] O VS Code usa o interpretador `.venv` (aparece na barra inferior)
- [ ] Você parou em um breakpoint e viu os valores no painel *Variables*
- [ ] Você corrigiu o bug e o commit tem mensagem `fix: ...`
- [ ] Nenhum `breakpoint()` ou `print` de depuração foi commitado (`git diff --staged` confere)
- [ ] Escreveu (em um arquivo `docs/ajuda.md`, sem commitar segredos) uma pergunta de ajuda no formato do passo 4

<details><summary>Solução de referência</summary>

```python
from decimal import Decimal

def price_with_tax(price: Decimal, rate: Decimal) -> Decimal:
    if rate < 0:
        raise ValueError("rate must be >= 0")
    return price * (1 + rate)

print(price_with_tax(Decimal("100.00"), Decimal("0.10")))   # 110.0000
```
(Usamos `Decimal` para dinheiro; o porquê vem no Módulo 1.)
</details>

**3. Desafio (opcional)**
Pegue um erro real que você já recebeu (ou provoque `KeyError`, `IndexError`, `AttributeError`) e escreva uma frase explicando a causa para alguém leigo.

## 🎤 Na entrevista
- **Como você investiga um bug?** Reproduzo de forma mínima, leio o traceback de baixo para cima, formulo uma hipótese, confirmo com breakpoint ou log, corrijo, escrevo um teste que teria pego o bug e só então commito.
- **Você usa IA para programar? Como garante a qualidade?** Uso para explicar erros e acelerar tarefas repetitivas, mas leio, entendo e testo tudo; não colo segredos; confiro APIs na documentação oficial; sou responsável pelo código que entrego.
- **Qual a diferença entre `print` e um debugger?** O `print` mostra o que você decidiu imprimir; o debugger pausa o programa e permite inspecionar qualquer variável e andar linha a linha sem alterar o código.

## 📚 Para ir além
- 📄 Documentação oficial: [VS Code: depuração de Python](https://code.visualstudio.com/docs/python/debugging). Breakpoints, `launch.json` e depuração de testes.
- 📄 Documentação oficial: [pdb (docs.python.org)](https://docs.python.org/3/library/pdb.html). Lista de comandos do depurador de terminal.
- 🎥 Vídeo (EN): *The Missing Semester* (MIT), aula “Debugging and Profiling”, em [missing.csail.mit.edu](https://missing.csail.mit.edu/). ~1h; assista à parte de depuração.
- 🏋️ Prática extra: escolha 3 erros da sua semana e reescreva cada um como “pergunta de ajuda” completa.

## ✅ Checklist da aula
- [ ] VS Code com Python + Ruff e interpretador `.venv`
- [ ] Parei em um breakpoint e inspecionei variáveis
- [ ] Li o traceback de baixo para cima sem pressa
- [ ] Escrevi uma pergunta de ajuda no formato certo
- [ ] Li 10 min de documentação em inglês
