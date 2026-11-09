# 17. Recursão e noções de Big-O

> ⏱️ ~1h30 · Módulo 1 · Pré-requisitos: [05](05-listas-tuplas.md), [06](06-dicts-sets.md), [16](16-decorators-context-managers.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Escrever funções recursivas com caso base e passo recursivo
- Explicar a pilha de chamadas e o limite de recursão
- Comparar versão recursiva, iterativa e com cache (memoização)
- Estimar a complexidade O(1), O(log n), O(n), O(n log n) e O(n²) de um trecho de código
- Medir tempo com `timeit` para confirmar a estimativa

## 🤔 Por que isso importa
Estruturas em árvore (categorias que têm subcategorias, comentários com respostas, pastas) são recursivas. E, mais importante, Big-O explica **por que uma página trava com 100 mil produtos**, por que o banco usa índices e por que N+1 consultas são um problema.

## 💡 Intuição (explicação simples)
- **Recursão** = **bonecas russas**: para abrir a boneca grande você abre a menor igual a ela, até chegar à menor de todas (caso base), e depois remonta.
- **Big-O** = **o preço que cresce com a fila**: atender 10 pessoas e 10 mil muda de “rapidinho” para “impossível” dependendo de como seu método escala. Não mede segundos; mede **como o trabalho cresce** quando a entrada cresce.

## 🔬 Como funciona por dentro
- Toda recursão precisa de **caso base** (para) e **passo** que se aproxima dele. Sem isso: `RecursionError`.
- Cada chamada ocupa um **frame** na pilha; o Python limita a profundidade (padrão ~1000, `sys.getrecursionlimit()`).
- `fib(n) = fib(n-1) + fib(n-2)` recalcula os mesmos valores exponencialmente; **memoização** (guardar resultados em dict) elimina isso.

| Notação | Nome | Exemplo | n = 1.000 → n = 2.000 |
|---|---|---|---|
| O(1) | constante | `dict[chave]`, `lista[i]` | igual |
| O(log n) | logarítmico | busca binária, índice B-tree | +1 passo |
| O(n) | linear | `x in lista`, percorrer | dobra |
| O(n log n) | | `sorted()` | pouco mais que dobra |
| O(n²) | quadrático | dois laços aninhados | quadruplica |
| O(2ⁿ) | exponencial | fib recursivo ingênuo | explode |

Big-O ignora constantes e termos menores: `3n² + 5n + 2` é O(n²). Descreve o **pior caso**, salvo indicação.

## 🛠️ Exemplo prático
**1. Recursão básica**
```python
def fatorial(n: int) -> int:
    if n <= 1:              # caso base
        return 1
    return n * fatorial(n - 1)   # passo recursivo

def somar_digitos(n: int) -> int:
    return n if n < 10 else n % 10 + somar_digitos(n // 10)

print(fatorial(5), somar_digitos(2024))
```
```text
120 8
```

**2. Limite de recursão**
```python
import sys
print(sys.getrecursionlimit())
def sem_fim(n):
    return sem_fim(n + 1)
sem_fim(0)
```
```text
1000
RecursionError: maximum recursion depth exceeded
```

**3. Recursão em árvore: categorias do MiniShop**
```python
categorias = {
    "nome": "Todos", "filhos": [
        {"nome": "Periféricos", "filhos": [{"nome": "Mouses", "filhos": []}, {"nome": "Teclados", "filhos": []}]},
        {"nome": "Cabos", "filhos": []},
    ],
}

def imprimir(cat, nivel=0):
    print("  " * nivel + cat["nome"])
    for f in cat["filhos"]:
        imprimir(f, nivel + 1)

def contar(cat):
    return 1 + sum(contar(f) for f in cat["filhos"])

imprimir(categorias)
print("total:", contar(categorias))
```
```text
Todos
  Periféricos
    Mouses
    Teclados
  Cabos
total: 5
```

**4. Fibonacci: ingênuo, memoizado e iterativo (e o tempo de cada um)**
```python
import timeit
from functools import lru_cache

def fib_lento(n):
    return n if n < 2 else fib_lento(n - 1) + fib_lento(n - 2)

@lru_cache(maxsize=None)
def fib_memo(n):
    return n if n < 2 else fib_memo(n - 1) + fib_memo(n - 2)

def fib_iter(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

print(fib_lento(25) == fib_memo(25) == fib_iter(25))
for nome, f in (("recursivo", fib_lento), ("memoizado", lambda n: (fib_memo.cache_clear(), fib_memo(n))[1]), ("iterativo", fib_iter)):
    print(f"{nome:<10} n=27: {timeit.timeit(lambda: f(27), number=3):.5f}s")
```
```text
True
recursivo  n=27: 0.04966s
memoizado  n=27: 0.00002s
iterativo  n=27: 0.00000s
```
(Valores variam; veja a proporção: o recursivo é O(2ⁿ), os outros O(n).)

**5. Medindo o crescimento (Big-O na prática)**
```python
import timeit

def linear(lista, alvo):                  # O(n)
    return alvo in lista

def com_set(conjunto, alvo):              # O(1) médio
    return alvo in conjunto

def duplicados_quadratico(v):             # O(n²)
    return any(v[i] == v[j] for i in range(len(v)) for j in range(i + 1, len(v)))

def duplicados_linear(v):                 # O(n)
    return len(set(v)) != len(v)

for n in (1_000, 2_000, 4_000):
    dados = list(range(n))
    t_quad = timeit.timeit(lambda: duplicados_quadratico(dados), number=1)
    t_lin = timeit.timeit(lambda: duplicados_linear(dados), number=1)
    print(f"n={n:>5}  O(n²)={t_quad:.4f}s  O(n)={t_lin:.6f}s")
```
```text
n= 1000  O(n²)=0.0132s  O(n)=0.000010s
n= 2000  O(n²)=0.0536s  O(n)=0.000101s
n= 4000  O(n²)=0.2160s  O(n)=0.000110s
```
Ao dobrar `n`, o quadrático leva ~4x mais; o linear cresce tão devagar que os tempos minúsculos têm ruído. É por isso que “funciona na minha máquina com 10 produtos” não prova nada com 100 mil.

## ⚠️ Erros comuns e boas práticas
| Mensagem / sintoma | Causa | Solução |
|---|---|---|
| `RecursionError: maximum recursion depth exceeded` | Sem caso base ou profundidade enorme | Corrija o caso base; ou use laço/pilha explícita |
| Recursão lentíssima (fib) | Subproblemas repetidos | Memoização (`lru_cache`) ou versão iterativa |
| Código “quadrático escondido” | `x in lista` dentro de laço, `lista.insert(0, x)` repetido | Use `set`/`dict`; `collections.deque` |
| Otimização prematura | Medir sem necessidade | Meça com `timeit`/profiler antes |

- Python **não** otimiza recursão de cauda; para profundidades grandes prefira iteração.
- Big-O é ferramenta de raciocínio, não de microotimização: antes de otimizar, meça.
- No Django, o O(n²) disfarçado mais comum é o **N+1** (uma consulta por item de uma lista), tema do Módulo 5 (aula 07).

## 🧠 Pausa para lógica
**Problema (estimar).** Qual a complexidade de cada trecho? (a) `for p in produtos: print(p)`; (b) `for a in produtos: for b in produtos: ...`; (c) `produtos[0]`; (d) `sorted(produtos)`; (e) `while n > 1: n //= 2`.

<details><summary>Dica</summary>
Conte quantas vezes o trecho mais interno roda em função de <code>n</code>. Dividir o problema ao meio a cada passo sugere logaritmo.
</details>

<details><summary>Solução comentada</summary>

(a) O(n). (b) O(n²): dois laços aninhados sobre `n`. (c) O(1). (d) O(n log n): ordenação por comparação. (e) O(log n): `n` cai pela metade a cada volta.

```python
n = 1_000_000
passos = 0
while n > 1:
    n //= 2
    passos += 1
print(passos)      # ~20 passos para 1 milhão: log2(1.000.000) ≈ 19,9
```
```text
19
```
</details>

**Variação mais difícil:** qual a complexidade de achar os 3 maiores de uma lista com `sorted(l)[-3:]` versus `heapq.nlargest(3, l)`?

## 🧩 Exercícios
**1. Fixação**
Escreva `soma_lista(lista)` recursivamente e `potencia(base, exp)` recursivamente.

<details><summary>Solução</summary>

```python
def soma_lista(l):
    return 0 if not l else l[0] + soma_lista(l[1:])
def potencia(b, e):
    return 1 if e == 0 else b * potencia(b, e - 1)
print(soma_lista([1, 2, 3, 4]), potencia(2, 10))
```
```text
10 1024
```
(`l[1:]` copia a lista a cada chamada, o que torna `soma_lista` O(n²) em tempo: um bom exemplo de custo escondido.)
</details>

**2. Aplicação no projeto MiniShop**
Em `minishop_cli/categorias.py`, represente categorias em árvore e implemente `caminho(cat, nome)` (ex.: `Todos > Periféricos > Mouses`), `listar_folhas(cat)` e `profundidade(cat)`, de forma recursiva.

Critérios de pronto:
- [ ] Funções recursivas com caso base claro
- [ ] Testes pytest com árvore de 3 níveis e árvore de 1 nó
- [ ] Um teste com árvore de profundidade 50 (sem `RecursionError`)
- [ ] Commit `feat: add recursive category tree helpers`

<details><summary>Solução de referência</summary>

```python
def caminho(cat, alvo, prefixo=()):
    atual = prefixo + (cat["nome"],)
    if cat["nome"] == alvo:
        return " > ".join(atual)
    for f in cat["filhos"]:
        achado = caminho(f, alvo, atual)
        if achado:
            return achado
    return None

def listar_folhas(cat):
    if not cat["filhos"]:
        return [cat["nome"]]
    return [n for f in cat["filhos"] for n in listar_folhas(f)]

def profundidade(cat):
    return 1 + max((profundidade(f) for f in cat["filhos"]), default=0)

arv = {"nome": "Todos", "filhos": [{"nome": "Periféricos", "filhos": [{"nome": "Mouses", "filhos": []}]}, {"nome": "Cabos", "filhos": []}]}
print(caminho(arv, "Mouses"), listar_folhas(arv), profundidade(arv), caminho(arv, "X"))
```
```text
Todos > Periféricos > Mouses ['Mouses', 'Cabos'] 3 None
```
</details>

**3. Desafio (opcional)**
Resolva as Torres de Hanói com recursão (contando os movimentos para n = 1..10). Qual a complexidade?

## 🎤 Na entrevista
- **O que é Big-O?** Notação que descreve como o custo (tempo/memória) cresce com o tamanho da entrada, ignorando constantes; normalmente no pior caso.
- **Qual a complexidade de `x in lista` e `x in set`?** O(n) e O(1) em média, respectivamente.
- **Como evitar `RecursionError`?** Garantir o caso base, reduzir a profundidade, ou trocar por iteração/pilha explícita; memoizar quando há subproblemas repetidos.

## 📚 Para ir além
- 📄 Documentação oficial: [Complexidade de operações em Python](https://wiki.python.org/moin/TimeComplexity). Tabela de custos de list/dict/set.
- 📄 Documentação oficial: [`timeit`](https://docs.python.org/3/library/timeit.html). Como medir trechos de código.
- 🎥 Vídeo (EN): *CS50x* (Harvard), aula sobre algoritmos e Big-O, disponível em [cs50.harvard.edu/x](https://cs50.harvard.edu/x/). ⚠️ Escolha a aula “Algorithms” da edição vigente; duração ~1h30.
- 🏋️ Prática extra: meça `lista.insert(0, x)` vs `deque.appendleft(x)` para 100 mil elementos.

## ✅ Checklist da aula
- [ ] Escrevi 3 funções recursivas com caso base
- [ ] Provoquei um `RecursionError`
- [ ] Medi o crescimento com `timeit`
- [ ] Classifiquei 5 trechos de código por Big-O
- [ ] Fiz o commit do exercício
