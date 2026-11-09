# 13. POO II: herança, composição e dataclasses

> ⏱️ ~1h30 · Módulo 1 · Pré-requisitos: [12](12-poo-classes.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Criar subclasses, sobrescrever métodos e usar `super()`
- Explicar polimorfismo e *duck typing*
- Decidir entre herança e composição
- Usar `@dataclass` (incluindo `frozen`, `field` e `__post_init__`)
- Usar classes abstratas simples com `abc`

## 🤔 Por que isso importa
No Django você herda de `models.Model`, `View`, `TestCase`, `Form`. Entender herança e `super()` é ler o framework. Entender composição evita hierarquias frágeis. E `dataclass` elimina código repetitivo em objetos que só carregam dados (DTOs, itens de pedido).

## 💡 Intuição (explicação simples)
- **Herança** = “**é um**”: um `ProdutoDigital` *é um* `Produto` com algo a mais (link de download, sem frete).
- **Composição** = “**tem um**”: um `Pedido` *tem* itens e *tem* um cliente; não *é* um item.
- **Polimorfismo** = o mesmo botão “pagar” funcionando para cartão, Pix ou boleto; quem chama não precisa saber qual é.
- **Dataclass** = um **formulário pré-impresso**: você lista os campos e o Python escreve o resto.

## 🔬 Como funciona por dentro
- Ao chamar `obj.metodo()`, o Python procura em `type(obj)` e depois nas classes-base na ordem do **MRO** (`Classe.__mro__`).
- `super()` delega para a próxima classe no MRO. Em subclasses, chame `super().__init__(...)` para inicializar a parte herdada.
- **Duck typing**: “se anda e grasna como pato, é pato”. Não importa a classe, basta ter o método.
- Regra prática: **prefira composição à herança**. Herança acopla a subclasse aos detalhes da base.
- `@dataclass` gera `__init__`, `__repr__` e `__eq__` a partir das anotações. `frozen=True` torna imutável; `field(default_factory=list)` evita o bug do padrão mutável.

## 🛠️ Exemplo prático
**1. Herança e `super()`**
```python
from decimal import Decimal

class Produto:
    def __init__(self, nome, preco):
        self.nome, self.preco = nome, Decimal(preco)
    def frete(self):
        return Decimal("15.00")
    def descricao(self):
        return f"{self.nome} (R$ {self.preco})"

class ProdutoDigital(Produto):
    def __init__(self, nome, preco, url):
        super().__init__(nome, preco)       # inicializa a parte herdada
        self.url = url
    def frete(self):                         # sobrescreve
        return Decimal("0")
    def descricao(self):
        return super().descricao() + " [digital]"

for p in (Produto("Mouse", "50"), ProdutoDigital("E-book", "30", "http://x/ebook")):
    print(p.descricao(), "frete", p.frete())     # polimorfismo
print(ProdutoDigital.__mro__[1].__name__, isinstance(ProdutoDigital("a", "1", "u"), Produto))
```
```text
Mouse (R$ 50) frete 15.00
E-book (R$ 30) [digital] frete 0
Produto True
```

**2. Duck typing**
```python
class Pix:
    def pagar(self, valor): return f"Pix de {valor}"
class Cartao:
    def pagar(self, valor): return f"Cartão de {valor}"

def checkout(meio, valor):
    return meio.pagar(valor)         # não importa a classe, só o método

print(checkout(Pix(), 10), "|", checkout(Cartao(), 20))
```
```text
Pix de 10 | Cartão de 20
```

**3. Composição (preferida)**
```python
from decimal import Decimal

class Item:
    def __init__(self, nome, preco, qtd):
        self.nome, self.preco, self.qtd = nome, Decimal(preco), qtd
    def subtotal(self): return self.preco * self.qtd

class Pedido:
    def __init__(self, cliente):
        self.cliente = cliente
        self.itens: list[Item] = []         # Pedido TEM itens
    def adicionar(self, item): self.itens.append(item)
    def total(self): return sum((i.subtotal() for i in self.itens), Decimal("0"))

pd = Pedido("Ana")
pd.adicionar(Item("Mouse", "49.90", 2))
pd.adicionar(Item("Cabo", "9.90", 1))
print(pd.total())
```
```text
109.70
```

**4. `dataclass`**
```python
from dataclasses import dataclass, field
from decimal import Decimal

@dataclass
class ItemPedido:
    sku: str
    preco: Decimal
    qtd: int = 1

    def __post_init__(self):               # validação depois do __init__ gerado
        if self.qtd <= 0:
            raise ValueError("qtd deve ser positiva")

    @property
    def subtotal(self) -> Decimal:
        return self.preco * self.qtd

@dataclass(frozen=True)
class Endereco:                            # imutável e hashable
    rua: str
    cidade: str

@dataclass
class Carrinho:
    itens: list[ItemPedido] = field(default_factory=list)   # nunca "= []"

i = ItemPedido("MS-01", Decimal("49.90"), 2)
print(i, i == ItemPedido("MS-01", Decimal("49.90"), 2), i.subtotal)
e = Endereco("Rua A", "Recife")
print(e, hash(e) == hash(Endereco("Rua A", "Recife")))
try:
    e.cidade = "X"
except Exception as ex:
    print(type(ex).__name__)
print(Carrinho(), Carrinho().itens is Carrinho().itens)
```
```text
ItemPedido(sku='MS-01', preco=Decimal('49.90'), qtd=2) True 99.80
Endereco(rua='Rua A', cidade='Recife') True
FrozenInstanceError
Carrinho(itens=[]) False
```

**5. Classe abstrata (contrato)**
```python
from abc import ABC, abstractmethod

class MeioPagamento(ABC):
    @abstractmethod
    def pagar(self, valor): ...

class Boleto(MeioPagamento):
    def pagar(self, valor): return f"Boleto de {valor}"

print(Boleto().pagar(5))
try:
    MeioPagamento()
except TypeError as e:
    print(e)
```
```text
Boleto de 5
Can't instantiate abstract class MeioPagamento without an implementation for abstract method 'pagar'
```

## ⚠️ Erros comuns e boas práticas
| Mensagem / sintoma | Causa | Solução |
|---|---|---|
| `AttributeError: 'ProdutoDigital' object has no attribute 'nome'` | Esqueceu `super().__init__()` na subclasse | Chame-o |
| `TypeError: Can't instantiate abstract class ... without an implementation for abstract method` | Subclasse não implementou o método abstrato | Implemente todos |
| `ValueError: mutable default <class 'list'> for field itens is not allowed: use default_factory` | `= []` em dataclass | `field(default_factory=list)` |
| `FrozenInstanceError` | Alterou campo de dataclass `frozen` | Crie outro objeto com `dataclasses.replace` |

- Hierarquias com mais de 2–3 níveis costumam ser sinal de problema; prefira composição.
- Não herde só para reaproveitar código; herde quando houver relação “é um” real.
- `isinstance` em excesso indica que o polimorfismo não está sendo usado.
- Dataclass para dados; classe comum quando há comportamento e invariantes complexos.

## 🧠 Pausa para lógica
**Problema (frete por estratégia).** Calcule o frete de um pedido de 3 formas: `Padrao` (R$ 15), `Expresso` (R$ 30 + 2% do valor) e `Retirada` (0). Adicionar um novo tipo não deve exigir alterar o código do pedido (sem `if/elif` por tipo).

<details><summary>Dica</summary>
Cada forma é um objeto com o método <code>calcular(valor)</code>. O pedido recebe o objeto e só chama o método.
</details>

<details><summary>Solução comentada</summary>

```python
from decimal import Decimal

class Padrao:
    def calcular(self, valor): return Decimal("15")
class Expresso:
    def calcular(self, valor): return Decimal("30") + valor * Decimal("0.02")
class Retirada:
    def calcular(self, valor): return Decimal("0")

def total_com_frete(valor, estrategia):
    return valor + estrategia.calcular(valor)

v = Decimal("200")
print({type(e).__name__: total_com_frete(v, e) for e in (Padrao(), Expresso(), Retirada())})
```
```text
{'Padrao': Decimal('215'), 'Expresso': Decimal('234.00'), 'Retirada': Decimal('200')}
```
Este é o padrão **Strategy** (Módulo 8). Novo tipo de frete = nova classe; o resto não muda (princípio aberto/fechado).
</details>

**Variação mais difícil:** implemente o frete como função em vez de classe. Qual versão é mais “pythônica”?

## 🧩 Exercícios
**1. Fixação**
Crie `Animal` com `falar()` e as subclasses `Cachorro` e `Gato`; percorra uma lista de animais chamando `falar()`.

<details><summary>Solução</summary>

```python
class Animal:
    def falar(self): raise NotImplementedError
class Cachorro(Animal):
    def falar(self): return "au"
class Gato(Animal):
    def falar(self): return "miau"
print([a.falar() for a in (Cachorro(), Gato())])
```
```text
['au', 'miau']
```
</details>

**2. Aplicação no projeto MiniShop**
Evolua a CLI: crie `ItemEstoque` (dataclass), `Produto` e `ProdutoDigital` (herança, sem estoque físico) e `Pedido` (composição de itens).

Critérios de pronto:
- [ ] `ProdutoDigital` sobrescreve `frete` e não controla estoque
- [ ] `Pedido` não herda de `list`; usa composição
- [ ] Dataclass com `default_factory` e validação em `__post_init__`
- [ ] Testes com `pytest` para o polimorfismo (lista mista de produtos)
- [ ] Commit `feat: add digital product and order composition`

<details><summary>Solução de referência</summary>

```python
from dataclasses import dataclass, field
from decimal import Decimal

@dataclass
class Produto:
    sku: str
    nome: str
    preco: Decimal
    qtd: int = 0
    def frete(self) -> Decimal: return Decimal("15")
    def controla_estoque(self) -> bool: return True

@dataclass
class ProdutoDigital(Produto):
    url: str = ""
    def frete(self) -> Decimal: return Decimal("0")
    def controla_estoque(self) -> bool: return False

@dataclass
class Pedido:
    cliente: str
    itens: list[tuple[Produto, int]] = field(default_factory=list)
    def adicionar(self, produto, qtd): self.itens.append((produto, qtd))
    def total(self):
        return sum((p.preco * q for p, q in self.itens), Decimal("0"))
    def frete(self):
        return max((p.frete() for p, _ in self.itens), default=Decimal("0"))

pd = Pedido("Ana")
pd.adicionar(Produto("MS-01", "Mouse", Decimal("49.90"), 5), 2)
pd.adicionar(ProdutoDigital("EB-01", "E-book", Decimal("30"), url="http://x"), 1)
print(pd.total(), pd.frete())
```
```text
129.80 15
```
</details>

**3. Desafio (opcional)**
Reescreva o frete com `typing.Protocol` em vez de classe abstrata (aula 14 apresenta tipos).

## 🎤 Na entrevista
- **Herança vs composição?** Herança modela “é um” e acopla subclasse à base; composição modela “tem um” e é mais flexível. Prefira composição.
- **O que é polimorfismo?** Tratar objetos de classes diferentes pela mesma interface; cada um responde a seu modo.
- **O que o `@dataclass` gera?** `__init__`, `__repr__`, `__eq__` (e, com opções, ordenação, `frozen` e hash) a partir dos campos anotados.

## 📚 Para ir além
- 📄 Documentação oficial: [Tutorial: herança](https://docs.python.org/3/tutorial/classes.html#inheritance). `super()` e herança múltipla.
- 📄 Documentação oficial: [`dataclasses`](https://docs.python.org/3/library/dataclasses.html). Todas as opções.
- 📄 Documentação oficial: [`abc`](https://docs.python.org/3/library/abc.html). Classes abstratas.
- 🏋️ Prática extra: modele `Funcionario`, `Gerente` e um relatório de folha polimórfico.

## ✅ Checklist da aula
- [ ] Usei `super()` corretamente
- [ ] Substituí um `if/elif` por polimorfismo
- [ ] Usei `dataclass` com `default_factory`
- [ ] Fiz o commit do exercício
