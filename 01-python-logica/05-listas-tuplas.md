# 05. Listas e tuplas

> ⏱️ ~1h30 · Módulo 1 · Pré-requisitos: [04](04-funcoes-escopo.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Criar, indexar, fatiar e modificar listas
- Usar os métodos mais comuns (`append`, `extend`, `pop`, `sort`, `sorted`)
- Explicar mutabilidade e a diferença entre referência e cópia
- Usar tuplas e desempacotamento
- Escolher entre lista e tupla

## 🤔 Por que isso importa
O catálogo, o carrinho e o resultado de uma consulta ao banco são sequências de itens. Confundir referência com cópia causa bugs em que um carrinho “altera” outro.

## 💡 Intuição (explicação simples)
- **Lista** = uma **lista de compras a lápis**: dá para riscar, acrescentar e reordenar.
- **Tupla** = uma **linha da tabela impressa**: um conjunto fixo de campos (nome, preço, quantidade). Não se altera, e isso é uma garantia.
- Duas variáveis para a mesma lista são **dois nomes para o mesmo papel**: se um escreve, o outro vê.

## 🔬 Como funciona por dentro
- Uma lista é um **array dinâmico de referências** para objetos. Acessar `lista[i]` é O(1); inserir no começo é O(n) (precisa deslocar tudo); `x in lista` é O(n) (percorre).
- Índices começam em 0; negativos contam do fim (`-1` é o último). Fatias `[ini:fim:passo]` incluem `ini` e excluem `fim`.
- **Mutável** (lista, dict, set) pode mudar no lugar; **imutável** (tupla, str, int) nunca muda, apenas se cria outro.
- `b = a` copia só a referência. `a.copy()` ou `a[:]` faz cópia **rasa** (os elementos internos continuam compartilhados); `copy.deepcopy` copia tudo.

| | Lista | Tupla |
|---|---|---|
| Mutável | Sim | Não |
| Uso típico | Coleção que cresce/muda | Registro fixo, retorno múltiplo, chave de dicionário |
| Sintaxe | `[1, 2]` | `(1, 2)`, ou `1, 2` |

## 🛠️ Exemplo prático
**1. Índices e fatias**
```python
p = ["Mouse", "Teclado", "Monitor", "Cabo", "Webcam"]
print(p[0], p[-1], p[1:3], p[:2], p[::2], p[::-1])
print(len(p), "Cabo" in p)
```
```text
Mouse Webcam ['Teclado', 'Monitor'] ['Mouse', 'Teclado'] ['Mouse', 'Monitor', 'Webcam'] ['Webcam', 'Cabo', 'Monitor', 'Teclado', 'Mouse']
5 True
```

**2. Modificando**
```python
c = ["Mouse"]
c.append("Teclado")
c.extend(["Cabo", "Webcam"])
c.insert(1, "Monitor")
ultimo = c.pop()
c.remove("Cabo")
print(c, ultimo)
```
```text
['Mouse', 'Monitor', 'Teclado'] Webcam
```

**3. Ordenar: `sort` (muda) vs `sorted` (novo)**
```python
precos = [120, 50, 900, 35]
print(sorted(precos), precos)              # original intacto
precos.sort(reverse=True)
print(precos)
itens = [("Mouse", 50), ("Cabo", 10), ("Teclado", 120)]
print(sorted(itens, key=lambda t: t[1]))   # ordena pelo 2º campo
```
```text
[35, 50, 120, 900] [120, 50, 900, 35]
[900, 120, 50, 35]
[('Cabo', 10), ('Mouse', 50), ('Teclado', 120)]
```

**4. Referência vs cópia**
```python
a = [1, 2, 3]
b = a                 # mesmo objeto
c = a.copy()          # outro objeto
b.append(4)
print(a, b, c, a is b, a is c)

matriz = [[0, 0], [0, 0]]
copia = matriz.copy() # rasa: as linhas internas continuam compartilhadas
copia[0][0] = 9
print(matriz)
```
```text
[1, 2, 3, 4] [1, 2, 3, 4] [1, 2, 3] True False
[[9, 0], [0, 0]]
```

**5. Tuplas e desempacotamento**
```python
produto = ("MS-01", "Mouse", 49.9)
sku, nome, preco = produto
print(sku, nome, preco)
primeiro, *resto = [10, 20, 30, 40]
print(primeiro, resto)
a, b = 1, 2
a, b = b, a
print(a, b)
```
```text
MS-01 Mouse 49.9
10 [20, 30, 40]
2 1
```
```python
t = (1, 2, 3)
t[0] = 9
```
```text
TypeError: 'tuple' object does not support item assignment
```

## ⚠️ Erros comuns e boas práticas
| Mensagem | Causa | Solução |
|---|---|---|
| `IndexError: list index out of range` | Índice fora do tamanho | Confira `len()`; cuidado com lista vazia |
| `TypeError: 'tuple' object does not support item assignment` | Tentou mudar uma tupla | Crie outra tupla ou use lista |
| `ValueError: list.remove(x): x not in list` | Item inexistente | Teste `if x in lista` antes |
| `ValueError: too many values to unpack (expected 2)` | Desempacotou número errado | Confira a quantidade ou use `*resto` |
| `lista.sort()` devolve `None` | `sort` altera no lugar | Use `sorted(lista)` se quer o resultado |

- Para matriz, não escreva `[[0]*3]*3` (as três linhas são a mesma lista). Use `[[0]*3 for _ in range(3)]`.
- `x in lista` em lista grande é lento; use `set` (aula 06).
- Prefira tupla para registros que não mudam.

## 🧠 Pausa para lógica
**Problema (busca).** Dada a lista de preços **ordenada**, ache se um valor existe. Compare a busca linear (percorre tudo) com a **binária** (divide ao meio) contando as comparações.

<details><summary>Dica</summary>
Mantenha dois limites (<code>baixo</code>, <code>alto</code>). Olhe o meio: se for maior que o alvo, descarte a metade de cima; se menor, a de baixo.
</details>

<details><summary>Solução comentada</summary>

```python
def linear(lista, alvo):
    comps = 0
    for x in lista:
        comps += 1
        if x == alvo:
            return True, comps
    return False, comps

def binaria(lista, alvo):
    baixo, alto, comps = 0, len(lista) - 1, 0
    while baixo <= alto:
        meio = (baixo + alto) // 2
        comps += 1
        if lista[meio] == alvo:
            return True, comps
        if lista[meio] < alvo:
            baixo = meio + 1
        else:
            alto = meio - 1
    return False, comps

dados = list(range(0, 1_000_000, 2))     # 500 mil números pares, ordenados
print(linear(dados, 999_998), binaria(dados, 999_998))
```
```text
(True, 500000) (True, 19)
```
Linear: ~500.000 comparações (O(n)). Binária: ~19 (O(log n)). É a ideia por trás dos **índices de banco** (Módulo 3). Só funciona se a lista estiver ordenada.
</details>

**Variação mais difícil:** use `bisect.bisect_left` da biblioteca padrão e confira com a sua.

## 🧩 Exercícios
**1. Fixação**
Dado `n = [5, 3, 8, 1]`, escreva (a) o maior sem usar `max`, (b) a lista ao contrário sem alterar `n`, (c) os dois menores.

<details><summary>Solução</summary>

```python
n = [5, 3, 8, 1]
maior = n[0]
for x in n:
    if x > maior: maior = x
print(maior, n[::-1], sorted(n)[:2], n)
```
```text
8 [1, 8, 3, 5] [1, 3] [5, 3, 8, 1]
```
</details>

**2. Aplicação no projeto MiniShop**
Em `src/catalogo.py`, mantenha o catálogo como lista de tuplas `(sku, nome, preco, qtd)`. Implemente `adicionar`, `remover_por_sku`, `ordenar_por_preco` e `mais_caros(n)`.

Critérios de pronto:
- [ ] `ordenar_por_preco` não altera o catálogo original
- [ ] `remover_por_sku` não quebra se o SKU não existe (devolve `False`)
- [ ] Preços em `Decimal`
- [ ] Commit `feat: add in-memory catalog with lists`

<details><summary>Solução de referência</summary>

```python
from decimal import Decimal

catalogo = []

def adicionar(cat, sku, nome, preco, qtd):
    cat.append((sku, nome, Decimal(preco), qtd))

def remover_por_sku(cat, sku):
    for i, item in enumerate(cat):
        if item[0] == sku:
            del cat[i]
            return True
    return False

def ordenar_por_preco(cat):
    return sorted(cat, key=lambda it: it[2])

def mais_caros(cat, n):
    return ordenar_por_preco(cat)[::-1][:n]

adicionar(catalogo, "A", "Mouse", "49.90", 3)
adicionar(catalogo, "B", "Monitor", "899.00", 1)
adicionar(catalogo, "C", "Cabo", "9.90", 20)
print([i[1] for i in mais_caros(catalogo, 2)], remover_por_sku(catalogo, "Z"), len(catalogo))
```
```text
['Monitor', 'Mouse'] False 3
```
</details>

**3. Desafio (opcional)**
Implemente `remover_duplicados(lista)` mantendo a ordem original, sem usar `set` diretamente. Depois repita usando `dict.fromkeys`.

## 🎤 Na entrevista
- **Qual a diferença entre lista e tupla?** Lista é mutável, tupla é imutável (e pode ser chave de dicionário). Tupla comunica “registro fixo”.
- **`b = a` copia a lista?** Não, só a referência; use `a.copy()` ou `list(a)`; `deepcopy` se houver objetos mutáveis dentro.
- **Qual o custo de `x in lista`?** O(n). Em `set`, em média O(1).

## 📚 Para ir além
- 📄 Documentação oficial: [Tutorial: mais sobre listas](https://docs.python.org/3/tutorial/datastructures.html). Todos os métodos com exemplos.
- 📄 Documentação oficial: [HowTo: ordenação](https://docs.python.org/3/howto/sorting.html). `sorted`, `key`, estabilidade.
- 📄 Documentação oficial: [`bisect`](https://docs.python.org/3/library/bisect.html). Busca binária pronta.
- 🏋️ Prática extra: rotacione uma lista em `k` posições (use fatias).

## ✅ Checklist da aula
- [ ] Reproduzi o bug de referência (`b = a`)
- [ ] Usei `sorted` com `key`
- [ ] Contei comparações linear vs binária
- [ ] Fiz o commit do exercício
