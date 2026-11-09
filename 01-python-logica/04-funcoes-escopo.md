# 04. Funções e escopo

> ⏱️ ~1h30 · Módulo 1 · Pré-requisitos: [03](03-lacos.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Definir funções com parâmetros posicionais, nomeados, padrão, `*args` e `**kwargs`
- Diferenciar `print` de `return`
- Explicar escopo local, global e a regra LEGB
- Evitar o bug do argumento padrão mutável
- Escrever docstrings e funções pequenas, com uma responsabilidade

## 🤔 Por que isso importa
Funções são a unidade de reaproveitamento e de teste. Views do Django, tarefas do Celery e testes do pytest são funções. Código sem funções vira um bloco de 300 linhas impossível de testar.

## 💡 Intuição (explicação simples)
Uma função é uma **receita de cozinha**: recebe ingredientes (parâmetros), segue passos e entrega um prato (`return`). Quem pede o prato não precisa saber a receita. O **escopo** é a cozinha: o que você pica lá dentro (variáveis locais) não aparece no salão.

## 🔬 Como funciona por dentro
- Cada chamada cria um **frame** com suas variáveis locais; ao terminar, ele desaparece.
- Ao ler um nome, o Python procura em ordem **LEGB**: **L**ocal → **E**nclosing (função externa) → **G**lobal (módulo) → **B**uilt-in.
- Atribuir a um nome dentro da função o torna **local**, mesmo que exista um global igual.
- Argumentos são passados **por referência ao objeto** (“por atribuição”): a função recebe o mesmo objeto. Se ele for mutável (lista, dict) e a função o modifica, quem chamou vê a mudança.
- Valores padrão são calculados **uma vez**, quando a função é definida, não a cada chamada.
- Sem `return`, a função devolve `None`.

## 🛠️ Exemplo prático
**1. Definir, chamar, devolver**
```python
def preco_com_desconto(preco, percentual=0):
    """Devolve o preço após aplicar o desconto percentual."""
    return preco * (100 - percentual) / 100

print(preco_com_desconto(200))
print(preco_com_desconto(200, 10))
print(preco_com_desconto(percentual=25, preco=200))   # argumentos nomeados
```
```text
200.0
180.0
150.0
```

**2. `print` não é `return`**
```python
def soma_print(a, b):
    print(a + b)

def soma_return(a, b):
    return a + b

x = soma_print(1, 2)
y = soma_return(1, 2)
print(x, y)
```
```text
3
None 3
```

**3. `*args` e `**kwargs`**
```python
def resumo(*itens, **opcoes):
    print(itens, opcoes)

resumo("a", "b", cor="azul", qtd=2)
valores = [3, 1, 2]
print(max(*valores))      # *lista "espalha" os elementos como argumentos
```
```text
('a', 'b') {'cor': 'azul', 'qtd': 2}
3
```

**4. Escopo (LEGB)**
```python
taxa = 0.1                      # global

def calcula(valor):
    taxa = 0.2                  # outra variável, local
    return valor * taxa

print(calcula(100), taxa)       # o global não mudou
```
```text
20.0 0.1
```
```python
contador = 0
def incrementa():
    contador += 1               # tenta ler e atribuir a um nome local ainda inexistente
incrementa()
```
```text
UnboundLocalError: cannot access local variable 'contador' where it is not associated with a value
```
Solução: receba e devolva o valor (`contador = incrementa(contador)`). O `global` existe, mas quase sempre indica um desenho ruim.

**5. A armadilha do argumento padrão mutável**
```python
def adiciona(item, lista=[]):
    lista.append(item)
    return lista

print(adiciona("a"))
print(adiciona("b"))            # surpresa: a mesma lista foi reutilizada

def adiciona_ok(item, lista=None):
    if lista is None:
        lista = []
    lista.append(item)
    return lista

print(adiciona_ok("a"), adiciona_ok("b"))
```
```text
['a']
['a', 'b']
['a'] ['b']
```

**6. Funções como valores**
```python
def dobro(x): return x * 2
aplicar = lambda f, v: f(v)
print(aplicar(dobro, 4), sorted(["bb", "a", "ccc"], key=len))
```
```text
8 ['a', 'bb', 'ccc']
```

## ⚠️ Erros comuns e boas práticas
| Mensagem | Causa | Solução |
|---|---|---|
| `UnboundLocalError: cannot access local variable 'x' where it is not associated with a value` | Atribuiu a `x` dentro da função antes de ler | Passe como parâmetro ou devolva o valor |
| `TypeError: f() takes 2 positional arguments but 3 were given` | Número de argumentos errado | Confira a assinatura (`help(f)`) |
| `TypeError: f() missing 1 required positional argument: 'b'` | Faltou argumento | Passe-o ou defina um padrão |
| Função “devolve `None`” | Esqueceu o `return` | Retorne o valor |

- Uma função, uma responsabilidade; se precisa de “e” para descrever, divida.
- Nunca use `[]` ou `{}` como valor padrão.
- Escreva docstring de uma linha e **type hints** (aula 14).
- Evite efeitos colaterais escondidos: se modifica o argumento, deixe claro no nome/documentação.

## 🧠 Pausa para lógica
**Problema (carrinho).** Escreva `total_carrinho(itens)` onde `itens` é uma lista de tuplas `(preco, qtd)` e devolve o total com `Decimal`. Depois acrescente o parâmetro opcional `cupom_percentual=0`.

<details><summary>Dica</summary>
Acumule <code>preco * qtd</code> e só no fim aplique o desconto e arredonde com <code>quantize</code>.
</details>

<details><summary>Solução comentada</summary>

```python
from decimal import Decimal

def total_carrinho(itens, cupom_percentual=0):
    total = sum((Decimal(p) * q for p, q in itens), Decimal("0"))
    total = total * (100 - Decimal(cupom_percentual)) / 100
    return total.quantize(Decimal("0.01"))

print(total_carrinho([("19.99", 3), ("5.50", 2)]))
print(total_carrinho([("19.99", 3), ("5.50", 2)], cupom_percentual=10))
```
```text
70.97
63.87
```
O `Decimal("0")` como valor inicial do `sum` evita misturar `int` com `Decimal` e também funciona com lista vazia.
</details>

**Variação mais difícil:** arredonde cada item antes de somar, ou só o total? Os resultados diferem? Qual a regra do negócio?

## 🧩 Exercícios
**1. Fixação**
Qual a saída? Explique.
```python
def f(x, acc=[]):
    acc.append(x)
    return len(acc)
print(f(1), f(2), f(3))
```
<details><summary>Solução</summary>

```python
def f(x, acc=[]):
    acc.append(x)
    return len(acc)
print(f(1), f(2), f(3))
```
```text
1 2 3
```
`1 2 3`: o `acc` padrão é criado uma vez e compartilhado entre as chamadas.
</details>

**2. Aplicação no projeto MiniShop**
Crie `src/produtos.py` com as funções `criar_produto(sku, nome, preco, qtd=0)` (devolve um dict), `valor_em_estoque(produto)` e `aplicar_desconto(produto, percentual)` (devolve **novo** dict, sem alterar o original).

Critérios de pronto:
- [ ] Preço sempre `Decimal`
- [ ] Docstring em cada função
- [ ] `aplicar_desconto` não modifica o dict original (prove com um `print`)
- [ ] Commit `feat: add product helper functions`

<details><summary>Solução de referência</summary>

```python
from decimal import Decimal

def criar_produto(sku, nome, preco, qtd=0):
    """Cria um produto como dict."""
    return {"sku": sku, "nome": nome, "preco": Decimal(preco), "qtd": qtd}

def valor_em_estoque(produto):
    """Preço x quantidade."""
    return produto["preco"] * produto["qtd"]

def aplicar_desconto(produto, percentual):
    """Devolve uma cópia com o preço reduzido."""
    novo = dict(produto)                        # cópia rasa basta aqui
    novo["preco"] = (produto["preco"] * (100 - Decimal(percentual)) / 100).quantize(Decimal("0.01"))
    return novo

p = criar_produto("MS-01", "Mouse", "49.90", 10)
q = aplicar_desconto(p, 10)
print(p["preco"], q["preco"], valor_em_estoque(p))
```
```text
49.90 44.91 499.00
```
</details>

**3. Desafio (opcional)**
Escreva `compor(f, g)` que devolve uma função `h(x) = f(g(x))`.

## 🎤 Na entrevista
- **Por que `def f(x, lista=[])` é perigoso?** O padrão é criado uma vez na definição e compartilhado entre chamadas; use `None` e crie a lista dentro.
- **O que é LEGB?** A ordem de busca de nomes: Local, Enclosing, Global, Built-in.
- **Qual a diferença entre `*args` e `**kwargs`?** `*args` reúne argumentos posicionais extras numa tupla; `**kwargs` reúne os nomeados num dicionário.

## 📚 Para ir além
- 📄 Documentação oficial: [Tutorial: definindo funções](https://docs.python.org/3/tutorial/controlflow.html#defining-functions). Argumentos padrão, `*args`, `**kwargs`.
- 📄 Documentação oficial: [Escopos e namespaces](https://docs.python.org/3/tutorial/classes.html#python-scopes-and-namespaces). Explicação oficial do LEGB.
- 🏋️ Prática extra: escreva `fatorial` e `fibonacci` com laço e confira com `math.factorial`.

## ✅ Checklist da aula
- [ ] Reproduzi o bug do argumento padrão mutável
- [ ] Provoquei um `UnboundLocalError` e o corrigi
- [ ] Minhas funções têm docstring
- [ ] Fiz o commit do exercício
