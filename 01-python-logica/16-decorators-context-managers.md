# 16. Decorators e context managers

> ⏱️ ~1h30 · Módulo 1 · Pré-requisitos: [04](04-funcoes-escopo.md), [09](09-arquivos-csv-json.md), [14](14-metodos-especiais-type-hints.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Explicar que funções são objetos e o que é um *closure*
- Escrever um decorator simples (com e sem argumentos) preservando metadados
- Usar `functools.lru_cache` e `functools.wraps`
- Explicar como `with` funciona e escrever um context manager
- Reconhecer decorators e context managers no Django (`@login_required`, `transaction.atomic`)

## 🤔 Por que isso importa
No Django você escreverá `@login_required`, `@require_POST`, `@receiver`, `@pytest.fixture`, `@app.task` (Celery) e `with transaction.atomic():` o tempo todo. A meta aqui é entender **o que acontece por baixo**, e escrever os seus quando precisar (log, tempo, cache, permissão).

## 💡 Intuição (explicação simples)
- **Decorator** = **embrulhar um presente**: o presente (função) continua o mesmo, mas ganha uma embalagem que faz algo antes e depois (medir o tempo, checar permissão).
- **Context manager** = **abrir e fechar a porta com garantia**: “entrar: acende a luz; sair (de qualquer jeito): apaga a luz”, mesmo que tenha dado problema lá dentro.

## 🔬 Como funciona por dentro
- Funções são objetos: podem ser passadas, devolvidas e guardadas.
- **Closure**: função interna que “lembra” as variáveis da externa, mesmo depois de ela terminar.
- `@deco` acima de `def f` é açúcar para `f = deco(f)`. O decorator recebe a função e devolve **outra** (o *wrapper*), que normalmente chama a original.
- `functools.wraps` copia nome e docstring da original para o wrapper (senão `f.__name__` vira `wrapper`).
- `with obj as x:` chama `obj.__enter__()` (valor vai para `x`) e, ao sair do bloco **de qualquer forma**, `obj.__exit__(tipo, valor, traceback)`. Se `__exit__` devolver `True`, a exceção é suprimida.
- `contextlib.contextmanager` transforma um gerador (com um `yield`) em context manager.

## 🛠️ Exemplo prático
**1. Closure**
```python
def multiplicador(n):
    def mult(x):
        return x * n          # "lembra" o n
    return mult

dobro = multiplicador(2)
print(dobro(5), multiplicador(10)(5))
```
```text
10 50
```

**2. Um decorator de tempo**
```python
import time
from functools import wraps

def cronometrar(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            print(f"{func.__name__} levou {(time.perf_counter() - t0) * 1000:.1f} ms")
    return wrapper

@cronometrar
def somar_ate(n):
    """Soma de 1 a n."""
    return sum(range(1, n + 1))

print(somar_ate(100_000))
print(somar_ate.__name__, "|", somar_ate.__doc__)
```
```text
somar_ate levou 0.8 ms
5000050000
somar_ate | Soma de 1 a n.
```
(O tempo varia por máquina.)

**3. Decorator com argumentos (uma camada a mais)**
```python
from functools import wraps

def exige_papel(papel):
    def deco(func):
        @wraps(func)
        def wrapper(usuario, *args, **kwargs):
            if papel not in usuario["papeis"]:
                raise PermissionError(f"requer o papel '{papel}'")
            return func(usuario, *args, **kwargs)
        return wrapper
    return deco

@exige_papel("admin")
def apagar_produto(usuario, sku):
    return f"{sku} apagado por {usuario['nome']}"

print(apagar_produto({"nome": "Ana", "papeis": ["admin"]}, "MS-01"))
try:
    apagar_produto({"nome": "Rui", "papeis": ["cliente"]}, "MS-01")
except PermissionError as e:
    print("negado:", e)
```
```text
MS-01 apagado por Ana
negado: requer o papel 'admin'
```
Isso é, em essência, o `@login_required` / `@permission_required` do Django.

**4. Cache com `lru_cache`**
```python
from functools import lru_cache

chamadas = 0

@lru_cache(maxsize=None)
def fib(n):
    global chamadas
    chamadas += 1
    return n if n < 2 else fib(n - 1) + fib(n - 2)

print(fib(80), "chamadas reais:", chamadas, fib.cache_info().hits)
```
```text
23416728348467685 chamadas reais: 81 78
```
Sem cache, `fib(80)` levaria séculos (aula 17). O cache é um dicionário: a mesma ideia da aula 06.

**5. Context manager na mão e com `contextlib`**
```python
from contextlib import contextmanager

class Transacao:
    def __enter__(self):
        print("BEGIN")
        return self
    def __exit__(self, tipo, valor, tb):
        print("ROLLBACK" if tipo else "COMMIT")
        return False                      # não engole a exceção

with Transacao():
    print("gravando...")

try:
    with Transacao():
        raise RuntimeError("falhou no meio")
except RuntimeError as e:
    print("capturado fora:", e)

@contextmanager
def secao(nome):
    print(f"[{nome}] início")
    try:
        yield
    finally:
        print(f"[{nome}] fim")

with secao("importação"):
    print("trabalhando")
```
```text
BEGIN
gravando...
COMMIT
BEGIN
ROLLBACK
capturado fora: falhou no meio
[importação] início
trabalhando
[importação] fim
```
É exatamente o que `with transaction.atomic():` faz no Django: `COMMIT` no sucesso e `ROLLBACK` em exceção (Módulos 3 e 5).

## ⚠️ Erros comuns e boas práticas
| Mensagem / sintoma | Causa | Solução |
|---|---|---|
| `TypeError: 'NoneType' object is not callable` ao usar o decorator | O wrapper não devolveu a função (esqueceu `return wrapper`) | Devolva o wrapper |
| Nome da função aparece como `wrapper` nos logs | Esqueceu `@wraps(func)` | Use `functools.wraps` |
| `TypeError: deco() missing 1 required positional argument` | Usou decorator com argumentos sem parênteses (`@exige_papel` em vez de `@exige_papel("admin")`) | Chame a fábrica |
| `lru_cache` devolve valor antigo | Função depende de estado externo | Só use em funções puras (mesma entrada, mesma saída) |
| `TypeError: unhashable type: 'list'` no `lru_cache` | Argumentos mutáveis | Use tuplas |

- Decorators devem ser pequenos e previsíveis; muita mágica dificulta depurar.
- Para recursos externos (arquivos, conexões, locks, transações), **sempre** `with`.
- O wrapper deve aceitar `*args, **kwargs` e devolver o resultado da original.

## 🧠 Pausa para lógica
**Problema (retentativa).** Escreva o decorator `tentar(vezes)` que repete a função se ela levantar `ConnectionError`, até `vezes` tentativas, e relança o erro na última. (Prévia de retentativas, Módulo 7.)

<details><summary>Dica</summary>
Três camadas: <code>tentar(vezes)</code> → <code>deco(func)</code> → <code>wrapper(*a, **k)</code> com um laço <code>for tentativa in range(vezes)</code>.
</details>

<details><summary>Solução comentada</summary>

```python
from functools import wraps

def tentar(vezes):
    def deco(func):
        @wraps(func)
        def wrapper(*a, **k):
            for tentativa in range(1, vezes + 1):
                try:
                    return func(*a, **k)
                except ConnectionError as e:
                    print(f"  tentativa {tentativa} falhou: {e}")
                    if tentativa == vezes:
                        raise
        return wrapper
    return deco

estado = {"n": 0}

@tentar(3)
def buscar():
    estado["n"] += 1
    if estado["n"] < 3:
        raise ConnectionError("sem rede")
    return "dados"

print(buscar())
```
```text
  tentativa 1 falhou: sem rede
  tentativa 2 falhou: sem rede
dados
```
Na vida real acrescenta-se espera entre tentativas (*backoff*) e só se tenta de novo erros transitórios (Módulo 7).
</details>

**Variação mais difícil:** acrescente espera crescente (1s, 2s, 4s) entre as tentativas.

## 🧩 Exercícios
**1. Fixação**
Escreva o decorator `log_chamada` que imprime o nome da função e os argumentos antes de executá-la.

<details><summary>Solução</summary>

```python
from functools import wraps
def log_chamada(f):
    @wraps(f)
    def w(*a, **k):
        print(f"chamando {f.__name__} com {a} {k}")
        return f(*a, **k)
    return w

@log_chamada
def somar(a, b): return a + b
print(somar(1, b=2))
```
```text
chamando somar com (1,) {'b': 2}
3
```
</details>

**2. Aplicação no projeto MiniShop**
Em `minishop_cli/utils.py`, crie o decorator `registrar_operacao` (grava em `operacoes.log` o nome da função, a hora e se deu certo) e o context manager `arquivo_seguro(caminho)` que escreve em arquivo temporário e só substitui o original no sucesso.

Critérios de pronto:
- [ ] Decorator usa `@wraps` e registra falha sem engolir a exceção
- [ ] `arquivo_seguro` mantém o arquivo antigo intacto se ocorrer exceção
- [ ] Testes pytest para os dois cenários (sucesso e falha)
- [ ] `operacoes.log` no `.gitignore`
- [ ] Commit `feat: add operation log decorator and safe file context manager`

<details><summary>Solução de referência</summary>

```python
import os
from contextlib import contextmanager
from pathlib import Path

@contextmanager
def arquivo_seguro(caminho):
    tmp = Path(str(caminho) + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        try:
            yield f
        except BaseException:
            f.close()
            tmp.unlink(missing_ok=True)      # descarta o parcial
            raise
    os.replace(tmp, caminho)                 # troca atômica

Path("dados.txt").write_text("original", encoding="utf-8")
try:
    with arquivo_seguro("dados.txt") as f:
        f.write("novo parcial")
        raise RuntimeError("caiu")
except RuntimeError:
    pass
print(Path("dados.txt").read_text(encoding="utf-8"))
with arquivo_seguro("dados.txt") as f:
    f.write("completo")
print(Path("dados.txt").read_text(encoding="utf-8"))
```
```text
original
completo
```
</details>

**3. Desafio (opcional)**
Implemente `memoize` do zero (dicionário) e compare com `lru_cache` em `fib(35)`.

## 🎤 Na entrevista
- **O que é um decorator?** Função que recebe uma função e devolve outra (geralmente um wrapper), adicionando comportamento sem alterar o código original; `@d` equivale a `f = d(f)`.
- **Por que usar `functools.wraps`?** Preserva `__name__`, `__doc__` e outros metadados da função original.
- **O que o `with` garante?** Que `__exit__` seja chamado ao sair do bloco, com ou sem exceção; por isso é usado em arquivos, locks e transações.

## 📚 Para ir além
- 📄 Documentação oficial: [`functools`](https://docs.python.org/3/library/functools.html). `wraps`, `lru_cache`, `partial`.
- 📄 Documentação oficial: [`contextlib`](https://docs.python.org/3/library/contextlib.html). `contextmanager`, `suppress`, `ExitStack`.
- 📄 Documentação oficial: [Tipos de context manager](https://docs.python.org/3/library/stdtypes.html#context-manager-types). O protocolo `__enter__`/`__exit__`.
- 🏋️ Prática extra: leia o código-fonte de `login_required` no Django (docs.djangoproject.com) quando chegar ao Módulo 5.

## ✅ Checklist da aula
- [ ] Escrevi um decorator com `@wraps`
- [ ] Escrevi um decorator com argumentos
- [ ] Escrevi um context manager de duas formas
- [ ] Fiz o commit do exercício
