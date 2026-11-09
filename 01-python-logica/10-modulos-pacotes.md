# 10. Módulos e pacotes

> ⏱️ ~1h30 · Módulo 1 · Pré-requisitos: [09](09-arquivos-csv-json.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Dividir um programa em módulos e importá-los
- Organizar módulos em pacotes com `__init__.py`
- Explicar `sys.path` e como o Python encontra um `import`
- Usar `if __name__ == "__main__":`
- Evitar importação circular

## 🤔 Por que isso importa
O Django é um pacote de pacotes; seu projeto também será. `from apps.catalog.models import Product` só faz sentido se você entende módulos, pacotes e caminho de importação. Erros como `ModuleNotFoundError` e `ImportError` estão entre os mais frequentes.

## 💡 Intuição (explicação simples)
Um módulo é **uma gaveta etiquetada** com ferramentas relacionadas (um arquivo `.py`). Um pacote é **um armário de gavetas** (uma pasta). `import` é “abrir a gaveta X para usar o que está lá”. Se tudo ficar numa gaveta só, ninguém acha nada.

## 🔬 Como funciona por dentro
- Um **módulo** é um arquivo `.py`; ao ser importado pela primeira vez, o Python **executa o arquivo inteiro** uma vez e guarda o resultado em `sys.modules` (cache). Importar de novo reaproveita.
- Um **pacote** é uma pasta com módulos (tradicionalmente com `__init__.py`).
- O `import` procura em `sys.path`: pasta do script, depois bibliotecas padrão e `site-packages` da `.venv`.
- `__name__` vale `"__main__"` quando o arquivo é executado diretamente e o nome do módulo quando é importado. O padrão `if __name__ == "__main__":` separa “biblioteca” de “programa”.
- **Importação circular:** `a` importa `b` e `b` importa `a`. Resolva movendo código comum para um terceiro módulo, ou importando dentro da função.

## 🛠️ Exemplo prático
Montaremos este layout:
```text
loja/
├── __init__.py
├── precos.py
└── estoque/
    ├── __init__.py
    └── baixa.py
main.py
```
```python
"""Pacote da loja."""
```
```python
from decimal import Decimal

IMPOSTO = Decimal("0.10")

def com_imposto(valor: Decimal) -> Decimal:
    return (valor * (1 + IMPOSTO)).quantize(Decimal("0.01"))

print("precos.py foi executado:", __name__)

if __name__ == "__main__":
    print("rodando direto:", com_imposto(Decimal("100")))
```
```python
from .baixa import baixar   # reexporta: permite `from loja.estoque import baixar`
```
```python
from ..precos import com_imposto      # import relativo (.. = pacote pai)

def baixar(estoque: dict, sku: str, qtd: int) -> int:
    estoque[sku] -= qtd
    return estoque[sku]
```
```python
from decimal import Decimal
import loja.precos
from loja.estoque import baixar

print(loja.precos.com_imposto(Decimal("50")))
print(baixar({"MS-01": 5}, "MS-01", 2))
```

**1. Executar o programa principal** (a primeira linha mostra que o módulo é executado uma vez, ao importar)
```bash
python main.py
python -m loja.precos
```
```text
precos.py foi executado: loja.precos
55.00
3
precos.py foi executado: __main__
rodando direto: 110.00
```
**2. Cache de módulos e `sys.path`**
```python
import sys
import loja.precos          # já importado? não executa de novo
print("loja.precos" in sys.modules, sys.path[0] != "")
import math, random
print(math.sqrt(16), random.Random(1).randint(1, 6))
from math import pi as PI   # apelido
print(round(PI, 4))
```
```text
precos.py foi executado: loja.precos
True True
4.0 2
3.1416
```

**3. Quando o módulo não existe**
```python
import modulo_inexistente
```
```text
ModuleNotFoundError: No module named 'modulo_inexistente'
```

## ⚠️ Erros comuns e boas práticas
| Mensagem | Causa | Solução |
|---|---|---|
| `ModuleNotFoundError: No module named 'loja'` | Rodou de uma pasta onde `loja/` não está no `sys.path` | Rode da raiz do projeto (`python main.py`, `python -m pacote.modulo`) |
| `ImportError: cannot import name 'x' from 'y'` | Nome inexistente, grafia errada ou importação circular | Confira o nome; veja se há ciclo |
| `ImportError: attempted relative import with no known parent package` | Executou o arquivo com import relativo diretamente | Use `python -m loja.estoque.baixa` |
| Seu arquivo se chama `random.py`/`json.py` | **Sombreia** o módulo da biblioteca padrão | Renomeie o seu arquivo |

- Prefira `import` no topo, agrupados: biblioteca padrão, terceiros, seu código (o Ruff organiza isso).
- Evite `from x import *` (polui o namespace e esconde a origem dos nomes).
- Código com efeito colateral no nível do módulo (abrir conexão, `print`) é armadilha: coloque dentro de funções.

## 🧠 Pausa para lógica
**Problema (ciclo).** `pedidos.py` importa `clientes.py` (para obter o cliente) e `clientes.py` importa `pedidos.py` (para listar pedidos). Como resolver sem copiar código?

<details><summary>Dica</summary>
Quem realmente depende de quem? Se só uma função de um módulo usa o outro, o import pode ficar dentro dela; ou extraia o que é comum para um terceiro módulo.
</details>

<details><summary>Solução comentada</summary>

Três saídas, da melhor para a pior:
1. **Reorganizar:** criar `modelos.py` com as classes `Cliente` e `Pedido`; `clientes.py` e `pedidos.py` importam de `modelos` (sem ciclo).
2. **Inverter a dependência:** `pedidos` conhece `clientes`, mas `clientes` recebe os pedidos como parâmetro.
3. **Import tardio:** `from pedidos import listar` dentro da função que o usa (resolve, mas esconde o acoplamento).

Ciclo quase sempre indica responsabilidades misturadas (Módulo 8).
</details>

**Variação mais difícil:** desenhe o grafo de importações do seu projeto atual. Há algum ciclo?

## 🧩 Exercícios
**1. Fixação**
O que imprime `import loja.precos` duas vezes seguidas no mesmo programa? Por quê?

<details><summary>Solução</summary>

A mensagem “precos.py foi executado” aparece **uma vez**: o módulo é executado na primeira importação e guardado em `sys.modules`.
</details>

**2. Aplicação no projeto MiniShop**
Reorganize o código das aulas anteriores em `minishop_cli/` (pacote): `produtos.py`, `erros.py`, `persistencia.py`, `texto.py`.

Critérios de pronto:
- [ ] Pasta `minishop_cli/` com `__init__.py`
- [ ] `python -m minishop_cli.produtos` funciona (com `if __name__ == "__main__"`)
- [ ] Nenhum import circular
- [ ] Nenhum arquivo seu com nome de módulo padrão (`json.py`, `random.py` etc.)
- [ ] Commit `refactor: organize cli code into a package`

<details><summary>Solução de referência</summary>

```bash
mkdir minishop_cli && touch minishop_cli/__init__.py
git mv src/produtos.py src/erros.py src/persistencia.py src/texto.py minishop_cli/
# ajuste os imports: from .erros import MiniShopError
uv run python -m minishop_cli.produtos
```
</details>

**3. Desafio (opcional)**
Provoque de propósito um import circular e leia a mensagem de erro. Em seguida conserte com a opção 1.

## 🎤 Na entrevista
- **O que faz `if __name__ == "__main__":`?** Executa o bloco só quando o arquivo é rodado diretamente, não quando importado.
- **Diferença entre módulo e pacote?** Módulo é um arquivo `.py`; pacote é uma pasta de módulos (com `__init__.py`).
- **Como o Python encontra o que você importa?** Procura em `sys.modules` (cache) e depois em `sys.path`.

## 📚 Para ir além
- 📄 Documentação oficial: [Tutorial: módulos](https://docs.python.org/3/tutorial/modules.html). Módulos, pacotes e `sys.path`.
- 📄 Documentação oficial: [Sistema de importação](https://docs.python.org/3/reference/import.html). Referência detalhada (leitura avançada).
- 🏋️ Prática extra: rode `python -c "import sys; print(sys.path)"` dentro e fora da `.venv` e compare.

## ✅ Checklist da aula
- [ ] Montei um pacote com subpacote e imports relativos
- [ ] Provoquei um `ModuleNotFoundError` e o resolvi
- [ ] Usei `if __name__ == "__main__":`
- [ ] Fiz o commit do exercício
