# 03. Entrevista: Python

> ⏱️ ~1h30 · Módulo 16 · Pré-requisitos: Módulo 1, 7 e 10

## 🎯 Objetivos
Ao final desta aula você consegue:
- Prever a saída das 13 "pegadinhas" clássicas de Python e explicar o mecanismo
- Responder perguntas conceituais (mutabilidade, GIL, geradores, decorators) em 60–90 s
- Pensar em voz alta ao resolver um problema
- Dizer "não sei, mas eu faria assim" sem travar

## 🤔 Por que isso importa
A conversa técnica de júnior raramente testa framework; testa **fundamentos** e **raciocínio**. As mesmas ~15 armadilhas aparecem em quase todo processo.

## 💡 Intuição (explicação simples)
O entrevistador quer ver **como você pensa**: a resposta certa dita sem explicação vale menos que a quase certa com raciocínio claro. Treine falar o mecanismo ("a lista padrão é criada **uma vez**, na definição").

## 🔬 Como funciona por dentro
Roteiro de resposta (use sempre): **1) a resposta curta · 2) o mecanismo · 3) um exemplo · 4) como evitar o problema**.

Conceitos que mais caem, em uma frase cada:
- **Mutável × imutável:** `list/dict/set` mudam no lugar; `int/str/tuple` não (a tupla contém referências: se um elemento é mutável, ele muda).
- **`is` × `==`:** identidade × igualdade; use `is` só para `None`/singletons.
- **GIL:** em CPython, uma thread executa bytecode Python por vez; threads ajudam em E/S, não em CPU puro (use processos). Versões *free-threaded* existem como opção; confira a documentação da sua versão.
- **Gerador:** função com `yield`; produz valores sob demanda e **esgota**.
- **Decorator:** função que recebe e devolve função (`functools.wraps` preserva nome/docstring).
- **`*args/**kwargs`**, **context manager** (`with` garante `__exit__`), **compreensões**, **`dataclass`**, **type hints** (não são checados em tempo de execução).

## 🛠️ Exemplo prático
Arquivo executável: [`entrevista/python_pegadinhas.py`](../projeto/referencia-m16/entrevista/python_pegadinhas.py). **Antes de rodar, preveja cada saída por escrito.**

```bash
cd projeto/referencia-m16 && uv run python entrevista/python_pegadinhas.py
```
Saída real (Python 3.13):
```text
1) default mutável: [1, 2] [1, 2] [3]
2) closure tardia: [2, 2, 2] | corrigido: [0, 1, 2]
3) is x ==: True False | None: True
4) cópia rasa: [[1, 2, 99], [3]] | profunda: [[1, 2], [3]]
5) float: 0.30000000000000004 False | Decimal: True
6) gerador: [0, 1, 4] []
7) chaves 1, 1.0, True colapsam: {1: 'c'}
8) remover iterando: [4, 1, 3] | certo: [1, 3]
9) posicional/keyword: (1, 2, 3) | erro: args_kwargs.<locals>.f() takes 2 positional arguments but 3 were given
10) escopo: UnboundLocalError
   (finally executa antes de devolver)
12) finally: try
13) memória: 56 8056 bytes; tupla vazia: 40
11) sem await: coroutine | com await: 42
```
Explicações:
1. O valor padrão é avaliado **uma vez**; as duas primeiras chamadas devolvem a *mesma* lista (por isso `[1, 2]` duas vezes). Correção: `lista=None` e criar dentro.
2. As lambdas guardam a **variável** `i`, não o valor; ao chamar, `i` já vale 2. Correção: `lambda i=i: i`.
3. Duas listas iguais não são o mesmo objeto.
4. `copy()` copia só o nível de fora; a lista interna é compartilhada.
5. Binário não representa 0,1 exatamente. Para dinheiro: `Decimal` criado **de texto** (`Decimal("0.1")`, não `Decimal(0.1)`).
6. Gerador consumido não volta.
7. `1 == 1.0 == True` e têm o mesmo hash: viram **uma** chave (a primeira chave fica, o último valor vence).
8. Remover enquanto itera pula elementos: o resultado `[4, 1, 3]` ainda tem o 4 (par). Use compreensão.
9. `/` e `*` na assinatura: `a` só posicional, `c` só nomeado.
10. A atribuição `x += 1` torna `x` **local** na função inteira.
11. Sem `await` você tem um objeto coroutine, não o valor (e o Python avisa "never awaited"). Na saída, a linha 11 vem por último porque roda depois, em `asyncio.run`.
12. O `finally` executa mesmo com `return` no `try`.
13. `sys.getsizeof` mede o contêiner, não os objetos dentro dele.

> Observação: a pegadinha 13 mostra números **desta máquina e versão**; não decore valores, entenda o que se mede.

## 🧠 Pausa para lógica
`def f(x, acc=[]): acc.append(x); return acc` é chamada em duas requisições web diferentes dentro do mesmo processo. Que bug de produção isso causa e por que o teste unitário de uma chamada só não o pega?
<details><summary>Solução</summary>

A lista cresce entre requisições (estado global escondido): usuários veem dados uns dos outros. Teste de uma chamada passa; só um teste que chama **duas vezes** (ou o `ruff` com a regra B006) expõe.
</details>

## ⚠️ Erros comuns e boas práticas
- Responder de memória sem rodar: **sempre confirme no interpretador** (`python -i`).
- Dizer "Python é lento": diga *quando* importa (CPU puro) e o que você faz (índice, cache, fila, processo).
- Chutar quando não sabe. Prefira: "Não lembro o nome exato; pelo que entendo, X. Eu confirmaria na documentação."
- Mensagens reais: `TypeError: f() takes 2 positional arguments but 3 were given` (pegadinha 9) e `UnboundLocalError: cannot access local variable 'x' where it is not associated with a value`.

## 🧩 Exercícios
1. **(Fixação)** Preveja a saída e depois rode: `a = [1, 2]; b = a; b += [3]; print(a)` e `a = (1, 2); b = a; b += (3,); print(a)`.
2. **(Aplicação no MiniShop)** Abra `apps/` do seu MiniShop e ache um uso real de: compreensão, gerador, context manager, decorator, `dataclass`. Anote o arquivo e **explique em 60 s** cada um, em voz alta.
   - [ ] 5 exemplos reais, com arquivo e linha
   - [ ] Gravei (áudio) uma resposta e ouvi
3. **(Desafio)** Escreva sua própria pegadinha (3 linhas), rode, e explique o mecanismo.

<details><summary>Solução do exercício 1</summary>

`[1, 2, 3]` (a lista é mutável e `+=` altera no lugar: `a` e `b` são o mesmo objeto) e `(1, 2)` (a tupla é imutável: `+=` cria outra tupla e religa só `b`).
</details>

## 🎤 Na entrevista
**Qual a diferença entre lista e tupla?** Mutável × imutável; tupla é hashable se o conteúdo for (pode ser chave de dicionário); use tupla para registro de tamanho fixo. **O que é o GIL?** Trava que deixa uma thread por vez executar bytecode em CPython: threads servem para E/S; CPU → `multiprocessing`/fila de tarefas. **`__init__` × `__new__`?** `__new__` cria o objeto, `__init__` o inicializa (raramente você mexe em `__new__`).

## 📚 Para ir além
- 📄 [Python — Perguntas frequentes de design](https://docs.python.org/pt-br/3/faq/programming.html) (verificado em 2026-11-09)
- 📄 [Python — Modelo de dados](https://docs.python.org/pt-br/3/reference/datamodel.html)
- 📑 Banco de perguntas do curso: [`recursos/perguntas-entrevista.md`](../recursos/perguntas-entrevista.md)
- 🏋️ Prática extra: responda 10 perguntas do banco em voz alta, cronometrando 90 s cada.

## ✅ Checklist da aula
- [ ] Previ por escrito antes de rodar e acertei ≥ 10 das 13
- [ ] Sei explicar cada mecanismo sem ler
- [ ] Tenho 5 usos reais de recursos da linguagem no meu código
