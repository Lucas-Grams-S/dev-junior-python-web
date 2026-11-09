# Checkpoint — Módulo 1: Python e lógica de programação

> ⏱️ ~1h30 · Faça **sem consultar** as aulas na primeira tentativa. Cronometre: 30 min para o quiz, 60 min para a entrega.

## 📝 Quiz (10 questões)
1. Por que `0.1 + 0.2 == 0.3` é `False` em Python e qual tipo você usa para dinheiro?
2. Qual a saída de `print(bool([]), bool([0]), 7 // 2, -7 % 3)`?
3. O que acontece com `def f(x, acc=[]): acc.append(x); return acc` ao chamar `f(1)` e depois `f(2)`? Como corrigir?
4. Explique a diferença entre lista e tupla e entre lista e set quanto ao custo de `x in colecao`.
5. `b = a` (com `a` uma lista) copia a lista? Mostre como copiar de verdade.
6. Em que situações um bloco `try` com `except:` sem tipo é um problema? Escreva a forma correta de capturar erro de conversão de texto para inteiro.
7. Por que usar `with open(..., encoding="utf-8")`? Como gravar um `Decimal` em JSON sem perder precisão?
8. O que `@dataclass` gera e por que `field(default_factory=list)` é necessário?
9. Em que ponto um gerador difere de uma lista? Quando preferir cada um?
10. Classifique por Big-O: `x in lista`, `x in set`, busca binária, `sorted(lista)` e dois laços aninhados sobre `n`.

<details><summary>Gabarito</summary>

1. `float` usa binário (IEEE 754) e 0,1/0,2 não têm representação exata. Para dinheiro, `Decimal` criado a partir de string (ou centavos inteiros).
2. `False True 3 2`. (Em Python, `-7 % 3` é `2`, pois o resto acompanha o sinal do divisor.)
3. O padrão `[]` é criado uma vez e compartilhado: `f(1)` devolve `[1]` e `f(2)` devolve `[1, 2]`. Correção: `acc=None` e `if acc is None: acc = []`.
4. Lista é mutável, tupla imutável (hashable se os itens forem). `x in lista` é O(n); `x in set` é O(1) em média (tabela hash).
5. Não, só copia a referência. Cópia: `a.copy()`, `list(a)` ou `a[:]`; `copy.deepcopy` se houver objetos mutáveis internos.
6. `except:` captura tudo (inclusive `KeyboardInterrupt`) e esconde bugs. Correto: `try: n = int(texto)` / `except ValueError:` tratando ou relançando com mensagem clara.
7. O padrão de codificação varia por sistema, e o `with` garante fechamento do arquivo mesmo com exceção. `Decimal` vira `str` (via `default=` do `json.dump`) e volta com `Decimal(texto)`.
8. `__init__`, `__repr__` e `__eq__` a partir das anotações. `default_factory` evita que todas as instâncias compartilhem a mesma lista.
9. Gerador produz valores sob demanda, usa pouca memória e só pode ser percorrido uma vez; lista guarda tudo e permite índice, `len` e várias passadas. Gerador para dados grandes/infinitos percorridos uma vez.
10. `x in lista` O(n); `x in set` O(1) médio; busca binária O(log n); `sorted` O(n log n); dois laços aninhados O(n²).
</details>

## 🛠️ Entrega prática
Repositório `minishop` com a **CLI de estoque** completa, na tag `v0.1-python-cli`:
- [ ] `python -m minishop_cli --help` com os subcomandos `add`, `repor`, `retirar`, `listar`, `relatorio`, `importar`
- [ ] Pacote `minishop_cli/` com `erros`, `modelos`, `repositorio`, `servico`, `importacao`, `cli`
- [ ] `Decimal` para dinheiro; persistência atômica em JSON; type hints nas assinaturas públicas
- [ ] `uv run pytest` verde com ≥ 22 testes (incluindo `parametrize`, `pytest.raises`, `tmp_path`, `capsys`)
- [ ] `uv run ruff check .` sem erros
- [ ] `seed/produtos.csv` com 20 produtos e importação funcionando
- [ ] README com instalação, exemplos de uso e como rodar os testes
- [ ] 10 exercícios de lógica das aulas resolvidos em `exercicios/` (um arquivo por pausa)
- [ ] Tag publicada: `git tag v0.1-python-cli && git push --tags`

**Prova de fogo (30 min, sem consultar):** crie `top_n(estoque, n)` que devolve os `n` produtos de maior valor em estoque, com teste. Se não conseguir, revise as aulas 05, 06 e 11.

## 🪞 Autoavaliação
Dê uma nota de 0 a 3 (0 = não sei; 3 = explico para alguém). Se algum item ficar em **0 ou 1**, refaça a aula indicada antes de seguir.

| Habilidade | Aula | Nota |
|---|---|---|
| Tipos, operadores, `Decimal` vs `float` | 01 | |
| Condicionais e valores limite | 02 | |
| Laços e acumuladores | 03 | |
| Funções, escopo, argumento padrão mutável | 04 | |
| Listas, tuplas, referência vs cópia | 05 | |
| Dicionários, sets, `Counter` | 06 | |
| Strings, f-strings, comprehensions | 07 | |
| Exceções e exceções próprias | 08 | |
| Arquivos, CSV, JSON | 09 | |
| Módulos, pacotes, imports | 10 | |
| pytest | 11 | |
| Classes, `@property` | 12 | |
| Herança, composição, dataclasses | 13 | |
| Dunder methods e type hints | 14 | |
| Iteradores e geradores | 15 | |
| Decorators e context managers | 16 | |
| Recursão e Big-O | 17 | |
| Projeto completo | 18–19 | |

## 🧠 Lógica: lista de verificação
Você resolveu, sem olhar as soluções: bissexto (02), paginação (03), busca binária (05), pedidos duplicados (06), CPF (07), entrada válida (08), importação CSV (09), ciclo de imports (10), Strategy de frete (13), Fibonacci gerador (15), retentativa (16) e Big-O (17)? Marque o que faltou e refaça.

➡️ Próximo: [Módulo 2 — Como a web funciona](../02-como-a-web-funciona/README.md).
