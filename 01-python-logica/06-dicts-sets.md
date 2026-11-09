# 06. Dicionários e sets

> ⏱️ ~1h30 · Módulo 1 · Pré-requisitos: [05](05-listas-tuplas.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Criar e percorrer dicionários e sets
- Contar e agrupar dados com `dict`, `defaultdict` e `Counter`
- Explicar por que a busca em `dict`/`set` é O(1) em média (tabela hash)
- Usar operações de conjuntos (união, interseção, diferença)
- Escolher entre list, tuple, dict e set

## 🤔 Por que isso importa
Um JSON de API vira dicionário. Cache é um dicionário. Detectar pedidos duplicados é um `set`. “Mais vendidos” é um `Counter`. É a estrutura mais usada no dia a dia em Python.

## 💡 Intuição (explicação simples)
- **Dicionário** = **agenda telefônica**: você procura pelo nome (chave) e vai direto ao número (valor), sem folhear todas as páginas.
- **Set** = **lista de convidados com nomes únicos**: só interessa se alguém está ou não, sem repetição e sem ordem.

## 🔬 Como funciona por dentro
- `dict` e `set` usam uma **tabela hash**: o `hash(chave)` calcula uma posição na tabela, então achar, inserir e remover custa **O(1) em média**, independentemente do tamanho. (Em lista, `in` é O(n).)
- Chaves precisam ser **hashable**: imutáveis (`str`, `int`, `tuple` de imutáveis). Lista não pode ser chave.
- Desde o Python 3.7 o `dict` **preserva a ordem de inserção**.
- `set` não tem ordem nem duplicatas.

| Estrutura | Ordem | Duplicatas | Busca | Use para |
|---|---|---|---|---|
| `list` | sim | sim | O(n) | sequência |
| `tuple` | sim | sim | O(n) | registro fixo |
| `dict` | inserção | chaves únicas | O(1) | procurar por chave |
| `set` | não | não | O(1) | pertencimento, unicidade |

## 🛠️ Exemplo prático
**1. Dicionário básico**
```python
produto = {"sku": "MS-01", "nome": "Mouse", "preco": 49.9}
produto["qtd"] = 10                 # adiciona
print(produto["nome"], produto.get("cor"), produto.get("cor", "sem cor"))
for chave, valor in produto.items():
    print(chave, "=", valor)
print("sku" in produto, list(produto.keys()))
del produto["qtd"]
```
```text
Mouse None sem cor
sku = MS-01
nome = Mouse
preco = 49.9
qtd = 10
True ['sku', 'nome', 'preco', 'qtd']
```
```python
produto = {"sku": "MS-01"}
print(produto["cor"])
```
```text
KeyError: 'cor'
```

**2. Contar e agrupar**
```python
from collections import Counter, defaultdict

vendas = ["mouse", "teclado", "mouse", "cabo", "mouse", "teclado"]
c = Counter(vendas)
print(c, c.most_common(2))

por_categoria = defaultdict(list)
for nome, cat in [("Mouse", "perif"), ("Cabo", "acess"), ("Teclado", "perif")]:
    por_categoria[cat].append(nome)
print(dict(por_categoria))
```
```text
Counter({'mouse': 3, 'teclado': 2, 'cabo': 1}) [('mouse', 3), ('teclado', 2)]
{'perif': ['Mouse', 'Teclado'], 'acess': ['Cabo']}
```

**3. Sets**
```python
a = {1, 2, 3, 3, 2}
b = {3, 4}
print(a, a | b, a & b, a - b, 2 in a)
emails = ["a@x.com", "b@x.com", "a@x.com"]
print(set(emails), len(set(emails)) != len(emails))   # há duplicatas?
```
```text
{1, 2, 3} {1, 2, 3, 4} {3} {1, 2} True
{'a@x.com', 'b@x.com'} True
```

**4. Medindo: lista vs set**
```python
import timeit
n = 200_000
lista = list(range(n))
conj = set(lista)
t_lista = timeit.timeit(lambda: (n - 1) in lista, number=200)
t_set = timeit.timeit(lambda: (n - 1) in conj, number=200)
print(f"lista: {t_lista:.4f}s  set: {t_set:.6f}s  (set ~{t_lista / t_set:,.0f}x mais rápido)")
```
```text
lista: 0.1584s  set: 0.000008s  (set ~18,979x mais rápido)
```
(Os tempos variam por máquina; a ordem de grandeza da diferença é o ponto.)

## ⚠️ Erros comuns e boas práticas
| Mensagem | Causa | Solução |
|---|---|---|
| `KeyError: 'cor'` | Chave inexistente | `d.get("cor")` ou `if "cor" in d` |
| `TypeError: unhashable type: 'list'` | Lista como chave ou dentro de set | Use `tuple` |
| `RuntimeError: dictionary changed size during iteration` | Alterou o dict enquanto percorria | Percorra uma cópia: `list(d.items())` |
| `{}` não é um set vazio | `{}` é dict vazio | Use `set()` |

- Use `dict.get` com padrão em vez de `try/except KeyError` quando a ausência é normal.
- Para contar, `Counter` é mais claro que `if chave in d: d[chave] += 1 else ...`.
- Não dependa da ordem de um `set`.

## 🧠 Pausa para lógica
**Problema (pedidos duplicados e idempotência).** Chegam webhooks de pagamento com um `event_id`. Se o mesmo `event_id` chegar duas vezes, o pedido não pode ser cobrado duas vezes. Escreva `processar(eventos)` que processa cada evento **uma única vez**.

<details><summary>Dica</summary>
Guarde os <code>event_id</code> já vistos num <code>set</code> e teste o pertencimento antes de processar.
</details>

<details><summary>Solução comentada</summary>

```python
def processar(eventos):
    vistos = set()
    processados = []
    for ev in eventos:
        if ev["event_id"] in vistos:       # O(1)
            continue                        # ignorar repetido = idempotência
        vistos.add(ev["event_id"])
        processados.append(ev["pedido"])
    return processados

eventos = [{"event_id": "e1", "pedido": 10}, {"event_id": "e2", "pedido": 11}, {"event_id": "e1", "pedido": 10}]
print(processar(eventos))
```
```text
[10, 11]
```
Em produção o conjunto de “já vistos” fica no banco (coluna `UNIQUE`) ou no Redis, não na memória do processo. Voltaremos a isso no Módulo 7.
</details>

**Variação mais difícil:** como detectar o *primeiro* par de pedidos que somam exatamente R$ 100 em uma lista de valores, em O(n) usando um `set`? (Problema clássico “two-sum”.)

## 🧩 Exercícios
**1. Fixação**
Dada `palavras = ["a", "b", "a", "c", "b", "a"]`, produza (a) um `dict` de contagens sem usar `Counter`, (b) as palavras únicas ordenadas.

<details><summary>Solução</summary>

```python
palavras = ["a", "b", "a", "c", "b", "a"]
cont = {}
for p in palavras:
    cont[p] = cont.get(p, 0) + 1
print(cont, sorted(set(palavras)))
```
```text
{'a': 3, 'b': 2, 'c': 1} ['a', 'b', 'c']
```
</details>

**2. Aplicação no projeto MiniShop**
Em `src/vendas.py`, a partir de uma lista de vendas `{"sku", "qtd"}`, gere o ranking dos 3 produtos mais vendidos (somando `qtd`) e a lista de SKUs que **não** venderam, comparando com o catálogo.

Critérios de pronto:
- [ ] Ranking com `Counter` somando quantidades (não ocorrências)
- [ ] “Sem vendas” usando diferença de sets
- [ ] Funciona com lista de vendas vazia
- [ ] Commit `feat: add sales ranking`

<details><summary>Solução de referência</summary>

```python
from collections import Counter

catalogo = {"MS-01", "TC-02", "CB-03", "MN-04"}
vendas = [{"sku": "MS-01", "qtd": 2}, {"sku": "CB-03", "qtd": 5}, {"sku": "MS-01", "qtd": 1}]

def ranking(vendas, n=3):
    c = Counter()
    for v in vendas:
        c[v["sku"]] += v["qtd"]
    return c.most_common(n)

def sem_vendas(catalogo, vendas):
    return sorted(catalogo - {v["sku"] for v in vendas})

print(ranking(vendas), sem_vendas(catalogo, vendas), ranking([]))
```
```text
[('CB-03', 5), ('MS-01', 3)] ['MN-04', 'TC-02'] []
```
</details>

**3. Desafio (opcional)**
Implemente um cache simples `cache = {}` para uma função lenta (`def preco_com_imposto(...)`) e conte acertos/erros de cache. (Prévia de `functools.lru_cache`.)

## 🎤 Na entrevista
- **Por que a busca em dict é rápida?** Usa tabela hash: calcula a posição pela chave, em O(1) médio.
- **O que pode ser chave de dicionário?** Objetos hashable (imutáveis), como `str`, `int`, `tuple` de imutáveis; não lista nem dict.
- **Como remover duplicatas mantendo a ordem?** `list(dict.fromkeys(lista))`.

## 📚 Para ir além
- 📄 Documentação oficial: [Tutorial: dicionários e sets](https://docs.python.org/3/tutorial/datastructures.html#dictionaries). Operações e laços.
- 📄 Documentação oficial: [`collections`](https://docs.python.org/3/library/collections.html). `Counter`, `defaultdict`, `deque`.
- 📄 Documentação oficial: [Complexidade das operações](https://wiki.python.org/moin/TimeComplexity). Tabela de custos de list, dict e set.
- 🏋️ Prática extra: resolva “two-sum” em O(n) com dict.

## ✅ Checklist da aula
- [ ] Medi lista vs set com `timeit`
- [ ] Usei `Counter` e `defaultdict`
- [ ] Entendi hashable e por que lista não é chave
- [ ] Fiz o commit do exercício
