# 03. Laços

> ⏱️ ~1h30 · Módulo 1 · Pré-requisitos: [02](02-condicionais.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Repetir ações com `for` e `while`
- Usar `range`, `enumerate` e `zip`
- Controlar o fluxo com `break`, `continue` e `else` do laço
- Acumular resultados (soma, contagem, máximo) em um laço
- Evitar laços infinitos e erros *off-by-one*

## 🤔 Por que isso importa
Processar 50 produtos, percorrer linhas de um arquivo, tentar de novo uma chamada que falhou: tudo é repetição. Paginação (offset/limit) é um laço com aritmética de índices.

## 💡 Intuição (explicação simples)
- `for` é **passar pela fila do caixa atendendo uma pessoa de cada vez**: você sabe quem está na fila.
- `while` é **“enquanto a panela estiver fria, continue mexendo”**: você repete até uma condição mudar, sem saber quantas vezes.

## 🔬 Como funciona por dentro
- `for x in coisa:` pede a `coisa` um **iterador** e chama `next()` até acabar (a aula 15 mostra isso por dentro). Funciona com listas, strings, dicionários, arquivos, `range`.
- `range(a, b, passo)` gera números de `a` até **`b - 1`** (o fim não entra). `range(5)` = 0,1,2,3,4.
- `while cond:` testa a condição **antes** de cada volta. Se nada altera a condição, o laço é infinito.
- `break` sai do laço; `continue` pula para a próxima volta; `else` do laço roda **se não houve `break`**.

## 🛠️ Exemplo prático
**1. `for` e `range`**
```python
for i in range(3):
    print("volta", i)
print(list(range(2, 10, 3)), list(range(5, 0, -2)))
```
```text
volta 0
volta 1
volta 2
[2, 5, 8] [5, 3, 1]
```

**2. `enumerate` e `zip`**
```python
produtos = ["Mouse", "Teclado", "Monitor"]
precos = [50, 120, 900]
for pos, nome in enumerate(produtos, start=1):
    print(pos, nome)
for nome, preco in zip(produtos, precos):
    print(f"{nome}: {preco}")
```
```text
1 Mouse
2 Teclado
3 Monitor
Mouse: 50
Teclado: 120
Monitor: 900
```

**3. Acumuladores**
```python
precos = [50, 120, 900, 35]
soma = 0
maior = precos[0]
for p in precos:
    soma += p
    if p > maior:
        maior = p
print("soma", soma, "média", soma / len(precos), "maior", maior)
```
```text
soma 1105 média 276.25 maior 900
```

**4. `while`, `break`, `continue` e `else`**
```python
tentativas = 0
while True:
    tentativas += 1
    if tentativas == 2:
        continue                  # pula o resto desta volta
    print("tentativa", tentativas)
    if tentativas >= 4:
        break

for n in [4, 6, 8]:
    if n % 2 == 1:
        print("achei ímpar", n)
        break
else:
    print("todos pares")         # só roda se o for terminou sem break
```
```text
tentativa 1
tentativa 3
tentativa 4
todos pares
```

**5. Armadilha: modificar a lista enquanto percorre**
```python
nums = [2, 4, 6, 8]
for n in nums:
    if n % 2 == 0:
        nums.remove(n)
print(nums)                       # esperado []
```
```text
[4, 8]
```
O resultado não é `[]`: remover itens desloca os índices e o laço “pula” elementos. Construa uma **nova** lista em vez disso (aula 07: comprehensions).

## ⚠️ Erros comuns e boas práticas
| Sintoma / mensagem | Causa | Solução |
|---|---|---|
| Programa não termina | `while` cuja condição nunca muda | Garanta que algo dentro altera a condição; `Ctrl+C` interrompe |
| Falta ou sobra um item | `range(n)` vai até `n-1` | Escreva um exemplo pequeno à mão |
| `IndexError: list index out of range` | Acessou `lista[len(lista)]` | O último índice é `len(lista) - 1` |
| `TypeError: 'int' object is not iterable` | `for x in 5:` | Use `range(5)` |

- Prefira `for item in lista` a `for i in range(len(lista))`; use `enumerate` se precisar do índice.
- Nunca altere a coleção que está sendo percorrida.
- Dê nomes que expliquem: `for product in products`, não `for p in x`.

## 🧠 Pausa para lógica
**Problema (paginação).** O catálogo tem `total` itens e cada página mostra `tamanho` itens. Escreva `pagina(itens, numero, tamanho)` (páginas começam em 1) e `total_paginas(total, tamanho)`. Cuidado com o *off-by-one*.

<details><summary>Dica</summary>
A página 1 começa no índice 0. Logo, <code>inicio = (numero - 1) * tamanho</code> e <code>fim = inicio + tamanho</code>. O número de páginas é o teto de <code>total / tamanho</code>, que dá para obter com inteiros: <code>-(-total // tamanho)</code>.
</details>

<details><summary>Solução comentada</summary>

```python
def total_paginas(total: int, tamanho: int) -> int:
    return -(-total // tamanho)             # teto sem float

def pagina(itens: list, numero: int, tamanho: int) -> list:
    inicio = (numero - 1) * tamanho         # página 1 -> índice 0
    return itens[inicio:inicio + tamanho]   # fatia ignora o excesso

itens = list(range(1, 24))                  # 23 itens
print(total_paginas(23, 10), pagina(itens, 1, 10), pagina(itens, 3, 10), pagina(itens, 4, 10))
```
```text
3 [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] [21, 22, 23] []
```
A fatia `[a:b]` nunca estoura o índice: a página 4 devolve `[]`. Este é exatamente o `OFFSET`/`LIMIT` do SQL (Módulo 3).
</details>

**Variação mais difícil:** e se `numero` for 0 ou negativo? Decida o comportamento e justifique.

## 🧩 Exercícios
**1. Fixação**
Escreva um laço que imprime a tabuada do 7 (de 1 a 10) e outro que soma os números pares de 1 a 100.

<details><summary>Solução</summary>

```python
for i in range(1, 11):
    print(f"7 x {i} = {7 * i}")
print(sum(n for n in range(1, 101) if n % 2 == 0))
```
```text
7 x 1 = 7
7 x 2 = 14
7 x 3 = 21
7 x 4 = 28
7 x 5 = 35
7 x 6 = 42
7 x 7 = 49
7 x 8 = 56
7 x 9 = 63
7 x 10 = 70
2550
```
</details>

**2. Aplicação no projeto MiniShop**
Em `src/relatorio.py`, dada uma lista de produtos (dicionários com `nome`, `preco`, `qtd`), imprima uma tabela numerada e o valor total do estoque.

Critérios de pronto:
- [ ] Usa `for` com `enumerate`
- [ ] Total calculado com acumulador e `Decimal`
- [ ] Lista vazia imprime “Estoque vazio” e não quebra
- [ ] Commit `feat: add stock report`

<details><summary>Solução de referência</summary>

```python
from decimal import Decimal

produtos = [
    {"nome": "Mouse", "preco": Decimal("49.90"), "qtd": 10},
    {"nome": "Teclado", "preco": Decimal("120.00"), "qtd": 4},
]

def relatorio(produtos):
    if not produtos:
        print("Estoque vazio")
        return
    total = Decimal("0")
    for n, p in enumerate(produtos, start=1):
        subtotal = p["preco"] * p["qtd"]
        total += subtotal
        print(f"{n:>2}. {p['nome']:<10} {p['qtd']:>3} x {p['preco']:>8} = {subtotal:>9}")
    print(f"Total: {total}")

relatorio(produtos)
relatorio([])
```
```text
 1. Mouse       10 x    49.90 =    499.00
 2. Teclado      4 x   120.00 =    480.00
Total: 979.00
Estoque vazio
```
</details>

**3. Desafio (opcional)**
Imprima um triângulo de asteriscos de altura `n` e depois um “tabuleiro” 8×8 alternando `#` e `.`.

## 🎤 Na entrevista
- **Quando usar `for` e quando `while`?** `for` quando se sabe o que percorrer; `while` quando se repete até uma condição mudar (ex.: tentar até funcionar).
- **O que `range(1, 5)` gera?** 1, 2, 3, 4 (o fim é exclusivo).
- **Para que serve o `else` de um `for`?** Executa se o laço terminou sem `break`, útil em buscas (“não encontrei”).

## 📚 Para ir além
- 📄 Documentação oficial: [Tutorial: for, range, break/continue/else](https://docs.python.org/3/tutorial/controlflow.html#for-statements). Descrição oficial dos laços.
- 📄 Documentação oficial: [`enumerate`](https://docs.python.org/3/library/functions.html#enumerate) e [`zip`](https://docs.python.org/3/library/functions.html#zip). Funções que simplificam laços.
- 🏋️ Prática extra: some os dígitos de um número inteiro usando `while` e `divmod(n, 10)`.

## ✅ Checklist da aula
- [ ] Previ a saída de `range` antes de rodar
- [ ] Provoquei um laço infinito e usei `Ctrl+C`
- [ ] Entendi por que não se altera a lista no laço
- [ ] Fiz o commit do exercício
