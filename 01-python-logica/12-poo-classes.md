# 12. POO I: classes e objetos

> ⏱️ ~1h30 · Módulo 1 · Pré-requisitos: [04](04-funcoes-escopo.md), [08](08-excecoes.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Definir classes com atributos e métodos
- Explicar `self` e o papel de `__init__`
- Diferenciar atributos de instância e de classe
- Aplicar encapsulamento com convenção `_privado` e `@property`
- Usar `@classmethod` e `@staticmethod`

## 🤔 Por que isso importa
O Django é orientado a objetos: um `Product` do ORM é uma classe, uma linha da tabela é um objeto, uma view baseada em classe herda de outra. Sem POO você usa o framework como receita de bolo; com POO você entende o que ele faz.

## 💡 Intuição (explicação simples)
Uma **classe é a planta de uma casa**; **objetos são as casas construídas** a partir dela. A planta define cômodos (atributos) e o que dá para fazer (métodos: abrir porta, ligar luz). Cada casa tem seu próprio estado: a luz de uma pode estar acesa e a de outra, não.

## 🔬 Como funciona por dentro
- `class Produto:` cria um objeto-classe. Chamar `Produto(...)` cria uma **instância** e executa `__init__` para inicializá-la.
- `self` é o próprio objeto: `p.aplicar_desconto(10)` é açúcar de `Produto.aplicar_desconto(p, 10)`. Por isso todo método de instância recebe `self` como 1º parâmetro.
- Atributos de **instância** (`self.preco`) vivem no `__dict__` de cada objeto. Atributos de **classe** (definidos no corpo da classe) são compartilhados por todas as instâncias.
- Python **não tem** `private` de verdade. Convenção: `_nome` = “uso interno, não mexa”. `@property` transforma um método em atributo calculado ou validado.
- `@classmethod` recebe a classe (`cls`) e serve como construtor alternativo; `@staticmethod` é uma função comum que mora na classe por organização.

## 🛠️ Exemplo prático
**1. Classe, instância, método**
```python
from decimal import Decimal

class Produto:
    def __init__(self, sku: str, nome: str, preco: Decimal, qtd: int = 0):
        self.sku = sku
        self.nome = nome
        self.preco = preco
        self.qtd = qtd

    def valor_em_estoque(self) -> Decimal:
        return self.preco * self.qtd

    def repor(self, n: int) -> None:
        self.qtd += n

mouse = Produto("MS-01", "Mouse", Decimal("49.90"), 10)
cabo = Produto("CB-03", "Cabo", Decimal("9.90"))
mouse.repor(5)
print(mouse.qtd, cabo.qtd, mouse.valor_em_estoque())
print(mouse)                      # representação padrão pouco útil (aula 14 melhora)
```
```text
15 0 748.50
<__main__.Produto object at 0x77e7fb6efa10>
```

**2. Atributo de classe vs de instância**
```python
class Contador:
    total = 0                     # da classe: compartilhado
    def __init__(self):
        Contador.total += 1
        self.numero = Contador.total   # da instância

a, b = Contador(), Contador()
print(a.numero, b.numero, Contador.total)
```
```text
1 2 2
```

**3. Encapsulamento com `@property`**
```python
from decimal import Decimal

class Produto:
    def __init__(self, nome, preco):
        self.nome = nome
        self.preco = preco        # passa pelo setter abaixo

    @property
    def preco(self) -> Decimal:
        return self._preco

    @preco.setter
    def preco(self, valor):
        valor = Decimal(valor)
        if valor < 0:
            raise ValueError("preço não pode ser negativo")
        self._preco = valor

p = Produto("Mouse", "49.90")
p.preco = "59.90"
print(p.preco)
try:
    p.preco = "-1"
except ValueError as e:
    print("erro:", e)
```
```text
59.90
erro: preço não pode ser negativo
```

**4. `@classmethod` e `@staticmethod`**
```python
class Produto:
    def __init__(self, sku, nome):
        self.sku, self.nome = sku, nome

    @classmethod
    def de_csv(cls, linha: str):          # construtor alternativo
        sku, nome = linha.split(",")
        return cls(sku, nome)

    @staticmethod
    def sku_valido(sku: str) -> bool:      # não usa self nem cls
        return len(sku) == 5 and sku[2] == "-"

p = Produto.de_csv("MS-01,Mouse")
print(p.sku, p.nome, Produto.sku_valido("MS-01"), Produto.sku_valido("X"))
```
```text
MS-01 Mouse True False
```

## ⚠️ Erros comuns e boas práticas
| Mensagem | Causa | Solução |
|---|---|---|
| `TypeError: Produto.__init__() missing 1 required positional argument: 'nome'` | Criou objeto sem os argumentos obrigatórios | Passe-os ou dê padrão |
| `TypeError: valor_em_estoque() takes 0 positional arguments but 1 was given` | Esqueceu o `self` na definição do método | `def valor_em_estoque(self):` |
| `AttributeError: 'Produto' object has no attribute 'estoque'` | Digitou o atributo errado ou não o criou no `__init__` | Defina todos os atributos no `__init__` |
| `NameError: name 'preco' is not defined` dentro do método | Esqueceu `self.` | `self.preco` |

- Defina **todos** os atributos de instância no `__init__`.
- Nada de lista/dict mutável como atributo de classe se for estado da instância (ficam compartilhados).
- Se a classe só guarda dados, a aula 13 mostra `dataclass`, que escreve o `__init__` por você.
- Prefira métodos que expressem intenção (`repor`, `vender`) a mexer em atributos de fora.

## 🧠 Pausa para lógica
**Problema (invariante).** Escreva `ContaEstoque` com `saldo` que **nunca** fica negativo. Métodos `entrada(n)` e `saida(n)`; `saida` maior que o saldo levanta `ValueError`. Como garantir que ninguém faça `conta.saldo = -5` de fora?

<details><summary>Dica</summary>
Guarde em <code>_saldo</code> e exponha só leitura via <code>@property</code> (sem setter).
</details>

<details><summary>Solução comentada</summary>

```python
class ContaEstoque:
    def __init__(self, saldo: int = 0):
        if saldo < 0:
            raise ValueError("saldo inicial negativo")
        self._saldo = saldo

    @property
    def saldo(self) -> int:          # só leitura
        return self._saldo

    def entrada(self, n: int) -> None:
        if n <= 0: raise ValueError("n deve ser positivo")
        self._saldo += n

    def saida(self, n: int) -> None:
        if n <= 0: raise ValueError("n deve ser positivo")
        if n > self._saldo: raise ValueError("saldo insuficiente")
        self._saldo -= n

c = ContaEstoque(5)
c.saida(3)
print(c.saldo)
try:
    c.saldo = -5
except AttributeError as e:
    print("bloqueado:", e)
```
```text
2
bloqueado: property 'saldo' of 'ContaEstoque' object has no setter
```
O objeto protege sua própria regra (**invariante**). É a ideia central de encapsulamento, e é o que o ORM e os serviços do Módulo 8 fazem.
</details>

**Variação mais difícil:** a classe é segura contra duas threads chamando `saida` ao mesmo tempo? (Spoiler: não; Módulo 7 e a transação do Módulo 3.)

## 🧩 Exercícios
**1. Fixação**
Crie a classe `Retangulo(largura, altura)` com `area()`, `perimetro()` e a propriedade `eh_quadrado`.

<details><summary>Solução</summary>

```python
class Retangulo:
    def __init__(self, largura, altura):
        self.largura, self.altura = largura, altura
    def area(self): return self.largura * self.altura
    def perimetro(self): return 2 * (self.largura + self.altura)
    @property
    def eh_quadrado(self): return self.largura == self.altura

r = Retangulo(3, 3)
print(r.area(), r.perimetro(), r.eh_quadrado)
```
```text
9 12 True
```
</details>

**2. Aplicação no projeto MiniShop**
Em `minishop_cli/produtos.py`, substitua o dict por uma classe `Produto` (`sku`, `nome`, `preco` validado, `qtd`) com `repor`, `retirar` (usando `EstoqueInsuficiente`), `valor_em_estoque` e o construtor alternativo `de_dict`/`para_dict`.

Critérios de pronto:
- [ ] `preco` é `Decimal` e rejeita valores negativos
- [ ] `retirar` mantém `qtd >= 0` sempre
- [ ] `para_dict` + `de_dict` fazem round-trip (útil para o JSON da aula 09)
- [ ] Testes pytest cobrindo os casos acima
- [ ] Commit `refactor: model Product as a class`

<details><summary>Solução de referência</summary>

```python
from decimal import Decimal

class EstoqueInsuficiente(Exception):
    pass

class Produto:
    def __init__(self, sku, nome, preco, qtd=0):
        self.sku, self.nome = sku, nome
        self.preco = preco
        self.qtd = qtd

    @property
    def preco(self): return self._preco
    @preco.setter
    def preco(self, v):
        v = Decimal(v)
        if v < 0: raise ValueError("preço negativo")
        self._preco = v

    def repor(self, n): self.qtd += n
    def retirar(self, n):
        if n > self.qtd:
            raise EstoqueInsuficiente(f"{self.sku}: pedido {n}, disponível {self.qtd}")
        self.qtd -= n
    def valor_em_estoque(self): return self.preco * self.qtd
    def para_dict(self): return {"sku": self.sku, "nome": self.nome, "preco": str(self.preco), "qtd": self.qtd}
    @classmethod
    def de_dict(cls, d): return cls(d["sku"], d["nome"], d["preco"], d["qtd"])

p = Produto("MS-01", "Mouse", "49.90", 3)
q = Produto.de_dict(p.para_dict())
print(q.para_dict() == p.para_dict(), q.valor_em_estoque())
```
```text
True 149.70
```
</details>

**3. Desafio (opcional)**
Faça `Produto` aceitar `qtd` apenas como `int` (rejeite `2.5`) usando uma propriedade.

## 🎤 Na entrevista
- **O que é `self`?** A referência ao objeto atual, passada automaticamente como 1º argumento dos métodos de instância.
- **Python tem atributos privados?** Não de verdade; usa-se a convenção `_nome` (e `__nome` faz *name mangling*, não segurança). Encapsulamento é por contrato.
- **Quando usar `@classmethod`?** Para construtores alternativos ou lógica que depende da classe e não da instância.

## 📚 Para ir além
- 📄 Documentação oficial: [Tutorial: classes](https://docs.python.org/3/tutorial/classes.html). Escopos, instâncias, atributos e métodos.
- 📄 Documentação oficial: [`property`](https://docs.python.org/3/library/functions.html#property). Getters, setters e propriedades.
- 🏋️ Prática extra: modele `Carrinho` com uma lista de itens e o método `total()`.

## ✅ Checklist da aula
- [ ] Criei classes com `__init__`, métodos e `@property`
- [ ] Entendi atributo de classe vs de instância
- [ ] Protegi uma regra de negócio dentro da classe
- [ ] Fiz o commit do exercício
