# Cheatsheet: Python básico (Módulo 1)

```python
# tipos: int float str bool None | dinheiro: Decimal("19.99")
x = [1, 2]; t = (1, 2); d = {"a": 1}; s = {1, 2}
[f(x) for x in xs if cond]; {k: v for ...}; (x for x in xs)   # lista, dict, gerador
d.get("k", padrao); Counter(xs).most_common(3); defaultdict(list)
with open(p, encoding="utf-8") as f: ...
try: ...
except ValueError as e: ...
else: ...
finally: ...
@dataclass class P: nome: str; preco: Decimal
def f(a, b=None, *args, **kw) -> int: ...
```
| Estrutura | Busca `x in` | Ordem | Duplicatas |
|---|---|---|---|
| list | O(n) | sim | sim |
| tuple | O(n) | sim | sim |
| dict | O(1) | inserção | chaves únicas |
| set | O(1) | não | não |
