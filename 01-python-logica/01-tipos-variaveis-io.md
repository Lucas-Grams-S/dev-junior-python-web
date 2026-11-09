# 01. Tipos, variáveis, operadores e entrada/saída

> ⏱️ ~1h30 · Módulo 1 · Pré-requisitos: [Módulo 0](../00-ambiente-ferramentas/README.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Criar variáveis e identificar os tipos `int`, `float`, `str`, `bool` e `None`
- Usar operadores aritméticos, de comparação e lógicos
- Converter entre tipos e explicar por que `0.1 + 0.2 != 0.3`
- Ler dados com `input()` e mostrar resultados com `print()`
- Usar `Decimal` para valores em dinheiro

## 🤔 Por que isso importa
Todo sistema recebe dados, guarda em variáveis, transforma e devolve. Preço, quantidade e nome do produto são exatamente isso. E o erro de usar `float` para dinheiro aparece em sistemas reais de pagamento.

## 💡 Intuição (explicação simples)
Uma variável é uma **etiqueta colada em uma caixa**. A caixa contém um valor; a etiqueta é o nome. Você pode mudar a etiqueta de caixa, ou trocar o que está dentro. O **tipo** é o formato da caixa: caixa de números, de texto, de sim/não. Não dá para somar texto com número da mesma forma que não dá para “somar” uma mala com uma data.

## 🔬 Como funciona por dentro
- Em Python, uma variável é um **nome que aponta para um objeto** na memória. `a = 10` cria o objeto `10` e liga o nome `a` a ele. `b = a` liga outro nome ao *mesmo* objeto.
- Todo objeto tem um tipo (`type(x)`). O Python é de **tipagem dinâmica** (o tipo está no objeto, não na variável) e **forte** (não converte `"3" + 4` sozinho).
- `float` guarda números em binário (IEEE 754), e muitas frações decimais (como 0,1) não cabem exatamente em binário; daí os erros minúsculos. `Decimal` guarda dígitos decimais exatos.

| Tipo | Exemplo | Observação |
|---|---|---|
| `int` | `42` | tamanho ilimitado |
| `float` | `3.14` | aproximado, nunca para dinheiro |
| `str` | `"olá"` | imutável |
| `bool` | `True`, `False` | subtipo de `int` (`True == 1`) |
| `NoneType` | `None` | “nenhum valor” |

| Operadores | |
|---|---|
| Aritméticos | `+ - * / // % **` (`/` sempre dá `float`; `//` divisão inteira; `%` resto) |
| Comparação | `== != < <= > >=` |
| Lógicos | `and or not` |

## 🛠️ Exemplo prático
Rode com `uv run arquivo.py` ou no interpretador (`uv run python`).

**1. Variáveis e tipos**
```python
nome = "Teclado"
preco = 199.9
quantidade = 3
ativo = True
sem_desconto = None
for v in (nome, preco, quantidade, ativo, sem_desconto):
    print(repr(v), type(v).__name__)
```
```text
'Teclado' str
199.9 float
3 int
True bool
None NoneType
```

**2. Operadores**
```python
print(7 / 2, 7 // 2, 7 % 2, 2 ** 10)
print(3 > 2 and not (1 == 2))
print(True + True)          # bool é int
```
```text
3.5 3 1 1024
True
2
```

**3. Conversão de tipos e erro clássico**
```python
idade = "30"
print(idade + 1)
```
```text
TypeError: can only concatenate str (not "int") to str
```
```python
idade = "30"
print(int(idade) + 1, str(30) + " anos", float("3.5"))
```
```text
31 30 anos 3.5
```

**4. O problema do `float` com dinheiro e a solução com `Decimal`**
```python
from decimal import Decimal

print(0.1 + 0.2, 0.1 + 0.2 == 0.3)
print(Decimal("0.1") + Decimal("0.2"), Decimal("0.1") + Decimal("0.2") == Decimal("0.3"))
total = Decimal("19.99") * 3
print(total, total.quantize(Decimal("0.01")))
```
```text
0.30000000000000004 False
0.3 True
59.97 59.97
```
Regra do curso: dinheiro é sempre `Decimal` criado **a partir de string** (`Decimal("19.99")`). `Decimal(19.99)` já nasce com o erro do `float`.

**5. Entrada e saída**
```python
from decimal import Decimal

nome = input("Produto: ")            # input() sempre devolve str
qtd = int(input("Quantidade: "))
preco = Decimal(input("Preço: "))
print(f"{qtd}x {nome} = R$ {qtd * preco:.2f}")
```
```text
Produto: Mouse
Quantidade: 2
Preço: 49.90
2x Mouse = R$ 99.80
```
(Na saída acima os valores digitados aparecem depois dos dois-pontos; no seu terminal, você digita cada um e aperta Enter.)

## ⚠️ Erros comuns e boas práticas
| Mensagem | Causa | Solução |
|---|---|---|
| `TypeError: can only concatenate str (not "int") to str` | Somou texto com número | `int(...)` ou `str(...)` |
| `ValueError: invalid literal for int() with base 10: 'abc'` | Converteu texto que não é número | Valide a entrada (aula 08 trata exceções) |
| `NameError: name 'preco' is not defined` | Usou antes de criar, ou digitou errado | Confira a grafia e a ordem |
| `SyntaxError: invalid syntax` | Faltou `:`, aspas ou parêntese | Veja a linha indicada **e a anterior** |

- Nomes: `snake_case`, em inglês no código do projeto (`unit_price`), descritivos. Evite `l`, `O`, `data2`.
- `=` atribui; `==` compara. Confundir os dois é erro frequente.
- Nunca compare `float` com `==`; use `math.isclose` ou, melhor, `Decimal`.

## 🧠 Pausa para lógica
**Problema.** Em uma compra de R$ 100,00 com 3 parcelas iguais, quanto vale cada parcela? A soma das parcelas precisa dar exatamente R$ 100,00. Como tratar os centavos que sobram?

<details><summary>Dica</summary>
Divida em centavos inteiros (`int`) e use `divmod` para obter quociente e resto. Distribua o resto de 1 em 1 centavo.
</details>

<details><summary>Solução comentada</summary>

```python
def parcelas(total_centavos: int, n: int) -> list[int]:
    base, resto = divmod(total_centavos, n)       # 10000 // 3 = 3333, sobra 1
    return [base + (1 if i < resto else 0) for i in range(n)]

p = parcelas(10000, 3)
print(p, sum(p))
```
```text
[3334, 3333, 3333] 10000
```
Trabalhar em centavos inteiros elimina o erro de arredondamento; o resto vai para as primeiras parcelas. A soma sempre fecha.
</details>

**Variação mais difícil:** se o resto for distribuído para as *últimas* parcelas, o que muda? E se `n` for 0?

## 🧩 Exercícios
**1. Fixação**
Sem executar, preveja a saída e depois confira: `print(10 // 3, 10 % 3, 10 / 4, type(10 / 5))`.

<details><summary>Solução</summary>

```python
print(10 // 3, 10 % 3, 10 / 4, type(10 / 5))
```
```text
3 1 2.5 <class 'float'>
```
`10 / 5` dá `2.0`: a divisão `/` sempre devolve `float`.
</details>

**2. Aplicação no projeto MiniShop**
Crie `src/produto_preco.py`: peça nome, preço e quantidade e mostre o total com 2 casas.

Critérios de pronto:
- [ ] Preço lido como `Decimal`, quantidade como `int`
- [ ] Saída no formato `2x Mouse = R$ 99.80`
- [ ] Rodou com `uv run src/produto_preco.py`
- [ ] Commit `feat: add price calculator script`

<details><summary>Solução de referência</summary>

```python
from decimal import Decimal

def total(preco: Decimal, qtd: int) -> Decimal:
    return (preco * qtd).quantize(Decimal("0.01"))

assert total(Decimal("49.90"), 2) == Decimal("99.80")
# no script real: nome = input(...); preco = Decimal(input(...)); qtd = int(input(...))
```
</details>

**3. Desafio (opcional)**
Peça um preço e um desconto percentual e mostre o preço final arredondado para centavos. O que ocorre se o desconto for `110`?

## 🎤 Na entrevista
- **Por que `0.1 + 0.2 != 0.3` em Python?** `float` usa binário (IEEE 754) e 0,1 e 0,2 não têm representação exata; a soma tem erro de ~1e-17. Para dinheiro usa-se `Decimal` ou centavos inteiros.
- **Python tem tipagem forte ou fraca? Dinâmica ou estática?** Forte (não converte tipos incompatíveis sozinho) e dinâmica (o tipo é verificado em execução).
- **O que significa `b = a` para listas?** Os dois nomes apontam para o mesmo objeto (veremos na aula 05).

## 📚 Para ir além
- 📄 Documentação oficial: [Tutorial Python: introdução informal](https://docs.python.org/3/tutorial/introduction.html). Números, strings e listas com exemplos.
- 📄 Documentação oficial: [`decimal`](https://docs.python.org/3/library/decimal.html). Aritmética decimal exata e arredondamento.
- 🎥 Vídeo (PT-BR): canal [Curso em Vídeo](https://www.youtube.com/@cursoemvideo), playlist de Python (aulas iniciais). ⚠️ link direto da playlist não verificado.
- 🏋️ Prática extra: calcule por escrito o resto de `-7 % 3` e confira no Python; explique o resultado.

## ✅ Checklist da aula
- [ ] Rodei os 5 exemplos e conferi a saída
- [ ] Provoquei um `TypeError` e um `ValueError`
- [ ] Sei explicar por que não uso `float` com dinheiro
- [ ] Fiz o commit do exercício
