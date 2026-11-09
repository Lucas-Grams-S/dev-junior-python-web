# 14. Métodos especiais e type hints

> ⏱️ ~1h30 · Módulo 1 · Pré-requisitos: [13](13-poo-heranca-dataclasses.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Implementar `__repr__`, `__str__`, `__eq__`, `__lt__`, `__len__` e `__iter__`
- Explicar por que métodos “dunder” fazem `len(x)`, `x == y` e `for` funcionarem
- Anotar funções e variáveis com tipos (`list[int]`, `X | None`, `Optional`)
- Rodar o `mypy` e ler seus erros
- Explicar que type hints **não** são verificados em execução

## 🤔 Por que isso importa
O ORM do Django usa `__str__` para mostrar objetos no Admin, `__len__`/`__iter__` para QuerySets. Type hints são a base do FastAPI/Pydantic (validação automática), tornam o código legível e ajudam o editor a achar bugs antes de rodar.

## 💡 Intuição (explicação simples)
- **Métodos especiais** são **“ganchos” que o Python chama por você**: ao escrever `len(carrinho)`, o Python pergunta ao objeto “qual seu `__len__`?”. É como o objeto responder a perguntas padrão do idioma.
- **Type hints** são **etiquetas nas caixas**: dizem o que deveria entrar e sair. O Python não fiscaliza, mas o editor e o `mypy` (o fiscal) leem as etiquetas.

## 🔬 Como funciona por dentro
- Operadores e funções embutidas chamam métodos dunder (de *double underscore*): `a == b` → `a.__eq__(b)`; `len(a)` → `a.__len__()`; `for x in a` → `a.__iter__()`; `print(a)` → `a.__str__()`; `a < b` → `a.__lt__(b)`.
- `__repr__` é para **desenvolvedores** (inequívoco, idealmente reconstrói o objeto); `__str__` é para **usuários**. Se só definir um, defina `__repr__`.
- Se você define `__eq__`, o Python remove o `__hash__` por padrão (objetos “iguais” precisam ter o mesmo hash). Dataclass cuida disso.
- Anotações ficam em `__annotations__` e são ignoradas pelo interpretador. Ferramentas (mypy, Pydantic, FastAPI) as leem.

## 🛠️ Exemplo prático
**1. `__repr__`, `__str__`, `__eq__`, `__lt__`**
```python
from decimal import Decimal
from functools import total_ordering

@total_ordering                      # gera <=, >, >= a partir de __eq__ e __lt__
class Produto:
    def __init__(self, sku: str, preco: Decimal):
        self.sku, self.preco = sku, preco
    def __repr__(self):
        return f"Produto(sku={self.sku!r}, preco={self.preco!r})"
    def __str__(self):
        return f"{self.sku} - R$ {self.preco}"
    def __eq__(self, outro):
        return isinstance(outro, Produto) and self.sku == outro.sku
    def __hash__(self):
        return hash(self.sku)
    def __lt__(self, outro):
        return self.preco < outro.preco

a, b = Produto("A", Decimal("10")), Produto("B", Decimal("5"))
print(repr(a)); print(a)
print(a == Produto("A", Decimal("99")), a > b, sorted([a, b]), {a, b} == {b, a})
```
```text
Produto(sku='A', preco=Decimal('10'))
A - R$ 10
True True [Produto(sku='B', preco=Decimal('5')), Produto(sku='A', preco=Decimal('10'))] True
```

**2. Contêiner: `__len__`, `__iter__`, `__getitem__`, `__contains__`**
```python
class Carrinho:
    def __init__(self):
        self._itens = []
    def adicionar(self, item): self._itens.append(item)
    def __len__(self): return len(self._itens)
    def __iter__(self): return iter(self._itens)
    def __getitem__(self, i): return self._itens[i]
    def __contains__(self, item): return item in self._itens
    def __bool__(self): return bool(self._itens)

c = Carrinho()
print(bool(c), len(c))
c.adicionar("mouse"); c.adicionar("cabo")
print(len(c), c[0], "cabo" in c, [i.upper() for i in c], list(reversed(c)))
```
```text
False 0
2 mouse True ['MOUSE', 'CABO'] ['cabo', 'mouse']
```

**3. Operadores e `__add__`**
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Dinheiro:
    centavos: int
    def __add__(self, o): return Dinheiro(self.centavos + o.centavos)
    def __mul__(self, n: int): return Dinheiro(self.centavos * n)
    def __str__(self): return f"R$ {self.centavos // 100},{self.centavos % 100:02d}"

print(Dinheiro(1999) + Dinheiro(501), Dinheiro(250) * 3)
```
```text
R$ 25,00 R$ 7,50
```

**4. Type hints**
```python
from decimal import Decimal

def total(itens: list[tuple[Decimal, int]], cupom: Decimal | None = None) -> Decimal:
    soma = sum((p * q for p, q in itens), Decimal("0"))
    return soma if cupom is None else soma - cupom

nome: str = "Mouse"
precos: dict[str, Decimal] = {"MS-01": Decimal("49.90")}
print(total([(Decimal("10"), 2)]), total.__annotations__["return"])
print(total([(Decimal("10"), "dois")]) if False else "o Python NÃO checa tipos em execução")
```
```text
20 <class 'decimal.Decimal'>
o Python NÃO checa tipos em execução
```

**5. Verificando com `mypy`**
```python
def dobrar(x: int) -> int:
    return x * 2

dobrar("abc")
```
```bash
python tipos.py; echo "saiu com código $?"
python -m mypy tipos.py || true
```
```text
saiu com código 0
tipos.py:4: error: Argument 1 to "dobrar" has incompatible type "str"; expected "int"  [arg-type]
Found 1 error in 1 file (checked 1 source file)
```
O programa **roda** (`"abc" * 2` é válido em Python), mas o `mypy` aponta o erro antes. Instalação: `uv add --dev mypy` (neste exemplo ele foi instalado só para rodar; a configuração completa do projeto fica no Módulo 10).

## ⚠️ Erros comuns e boas práticas
| Mensagem / sintoma | Causa | Solução |
|---|---|---|
| `TypeError: unhashable type: 'Produto'` | Definiu `__eq__` sem `__hash__` | Defina `__hash__` coerente (ou use `dataclass(frozen=True)`) |
| `TypeError: '<' not supported between instances of 'Produto' and 'Produto'` | Falta `__lt__` | Implemente (+ `@total_ordering`) |
| `print(objeto)` mostra `<__main__.Produto object at 0x...>` | Sem `__repr__`/`__str__` | Defina `__repr__` |
| mypy: `Incompatible types in assignment` | Atribuição contraria o tipo anotado | Corrija o valor ou o tipo |

- Escreva `__repr__` em todas as classes de domínio: facilita depurar e ler logs.
- Anote assinaturas públicas (parâmetros e retorno); variáveis locais só quando ajudar.
- Use `X | None` (Python 3.10+) em vez de `Optional[X]`; `list[int]` em vez de `List[int]`.
- Não implemente dunders “por esporte”; só os que fazem o objeto se comportar como o conceito pede.

## 🧠 Pausa para lógica
**Problema (ordenação estável).** Ordene produtos por preço crescente e, em empate de preço, por nome. Faça de duas formas: `key` com tupla, e `__lt__`.

<details><summary>Dica</summary>
Tuplas comparam elemento a elemento: <code>(preco, nome)</code> já resolve o desempate.
</details>

<details><summary>Solução comentada</summary>

```python
from decimal import Decimal
prods = [("Cabo", Decimal("10")), ("Mouse", Decimal("50")), ("Adaptador", Decimal("10"))]
print(sorted(prods, key=lambda p: (p[1], p[0])))          # preço, depois nome
print(sorted(prods, key=lambda p: (-p[1], p[0])))         # preço decrescente, nome crescente
```
```text
[('Adaptador', Decimal('10')), ('Cabo', Decimal('10')), ('Mouse', Decimal('50'))]
[('Mouse', Decimal('50')), ('Adaptador', Decimal('10')), ('Cabo', Decimal('10'))]
```
Para decrescente em campo não numérico, ordene em duas passadas: o `sorted` do Python é **estável**, então ordene primeiro pelo critério secundário e depois pelo principal.
</details>

**Variação mais difícil:** ordene por preço decrescente e nome *decrescente* sem negar nada, usando `reverse=True`.

## 🧩 Exercícios
**1. Fixação**
Por que `{Produto("A"), Produto("A")}` tem 2 elementos se `__eq__` compara SKUs? O que falta?

<details><summary>Solução</summary>

Falta `__hash__` coerente com `__eq__`. Sem ele, cada instância tem hash diferente (baseado na identidade); com `__hash__ = hash(self.sku)` o set reconhece a duplicata.
</details>

**2. Aplicação no projeto MiniShop**
Acrescente à classe `Produto` `__repr__`, `__str__`, `__eq__`/`__hash__` (por SKU) e anote todos os métodos. Crie `Estoque` com `__len__`, `__iter__` e `__contains__` (por SKU).

Critérios de pronto:
- [ ] `print(produto)` e `repr(produto)` são úteis
- [ ] `"MS-01" in estoque` e `len(estoque)` funcionam
- [ ] `uv run mypy minishop_cli` não reporta erros (ou ficam justificados)
- [ ] Testes pytest cobrindo `__eq__`, `__hash__` e `__contains__`
- [ ] Commit `feat: add dunder methods and type hints`

<details><summary>Solução de referência</summary>

```python
from decimal import Decimal

class Produto:
    def __init__(self, sku: str, nome: str, preco: Decimal, qtd: int = 0) -> None:
        self.sku, self.nome, self.preco, self.qtd = sku, nome, preco, qtd
    def __repr__(self) -> str:
        return f"Produto({self.sku!r}, {self.nome!r}, {self.preco!r}, {self.qtd!r})"
    def __str__(self) -> str:
        return f"{self.sku} {self.nome} (R$ {self.preco})"
    def __eq__(self, o: object) -> bool:
        return isinstance(o, Produto) and o.sku == self.sku
    def __hash__(self) -> int:
        return hash(self.sku)

class Estoque:
    def __init__(self) -> None:
        self._itens: dict[str, Produto] = {}
    def adicionar(self, p: Produto) -> None: self._itens[p.sku] = p
    def __len__(self) -> int: return len(self._itens)
    def __iter__(self):
        return iter(self._itens.values())
    def __contains__(self, sku: object) -> bool: return sku in self._itens

e = Estoque()
e.adicionar(Produto("MS-01", "Mouse", Decimal("49.90"), 3))
print(len(e), "MS-01" in e, "X" in e, [str(p) for p in e])
```
```text
1 True False ['MS-01 Mouse (R$ 49.90)']
```
</details>

**3. Desafio (opcional)**
Implemente `__enter__`/`__exit__` em uma classe `Transacao` (prévia da aula 16).

## 🎤 Na entrevista
- **Diferença entre `__str__` e `__repr__`?** `__str__` é a forma legível para o usuário final; `__repr__` é inequívoca para desenvolvedores (depuração/logs).
- **Type hints são verificados em execução?** Não. São metadados usados por ferramentas (mypy, editores, Pydantic, FastAPI).
- **O que acontece com `__hash__` ao definir `__eq__`?** O Python torna a classe não hashable, a menos que você defina `__hash__`.

## 📚 Para ir além
- 📄 Documentação oficial: [Modelo de dados: métodos especiais](https://docs.python.org/3/reference/datamodel.html#special-method-names). Lista completa de dunders.
- 📄 Documentação oficial: [`typing`](https://docs.python.org/3/library/typing.html). Tipos, `Protocol`, genéricos.
- 📄 Documentação oficial: [mypy: cheat sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html). Anotações mais usadas na prática.
- 🏋️ Prática extra: anote todas as funções do seu projeto e rode o `mypy` até zerar os erros.

## ✅ Checklist da aula
- [ ] Todas as classes de domínio têm `__repr__`
- [ ] Implementei um contêiner com `__len__`/`__iter__`
- [ ] Anotei as assinaturas e rodei o `mypy`
- [ ] Fiz o commit do exercício
