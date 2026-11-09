# Cheatsheet: django-orm

> Django 5.2 · aulas 5.04 a 5.07, 5.16 e 5.17. Exemplos com `Product`, `Category` e `Order` do MiniShop.

## Consultar
```python
Product.objects.all()                         # QuerySet (lazy: não vai ao banco ainda)
Product.objects.filter(is_active=True)        # WHERE
Product.objects.exclude(stock=0)              # WHERE NOT
Product.objects.get(sku="MOU-1")              # 1 objeto; DoesNotExist / MultipleObjectsReturned
Product.objects.order_by("price", "-id")      # ORDER BY (desempate por id)
Product.objects.first(), .last(), .count(), .exists()
Product.objects.values("sku", "price")        # dicionários
Product.objects.values_list("sku", flat=True) # lista simples
Product.objects.only("sku", "name")           # carrega só estes campos
Product.objects.distinct()
Product.objects.all()[:12]                    # LIMIT 12 (fatiar não executa até iterar)
```

## Lookups (`campo__operador`)
| Lookup | SQL |
|---|---|
| `name__icontains="mou"` | `ILIKE '%mou%'` |
| `name__istartswith`, `__iendswith` | começo / fim |
| `price__gte=10`, `__lt`, `__lte`, `__gt` | comparações |
| `sku__in=["A", "B"]` | `IN` |
| `price__range=(10, 50)` | `BETWEEN` |
| `description__isnull=True` | `IS NULL` |
| `category__slug="audio"` | atravessa a FK (`JOIN`) |
| `created_at__date=...`, `__year`, `__month` | partes da data |

## Combinar e comparar colunas
```python
from django.db.models import Q, F
Product.objects.filter(Q(name__icontains="x") | Q(sku__icontains="x"))      # OR
Product.objects.filter(~Q(is_active=False))                                 # NOT
OrderItem.objects.filter(unit_price__lt=F("product__price"))               # coluna × coluna (preço subiu desde a compra)
Product.objects.filter(pk=1).update(stock=F("stock") - 1)                   # atômico no banco
```

## Relacionamentos
```python
categoria.products.all()                      # related_name da FK (reverso)
Product.objects.filter(category__name="Áudio")
Product.objects.select_related("category")    # JOIN: FK / 1:1 (evita N+1)
Cart.objects.prefetch_related("items__product")   # consulta extra com IN: N:N / reverso
Prefetch("items", queryset=CartItem.objects.select_related("product"), to_attr="itens")
```

## Agregar
```python
from django.db.models import Count, Sum, Avg, Max, Min
Product.objects.aggregate(total=Sum("stock"), media=Avg("price"))           # dict, 1 resultado
Category.objects.annotate(n=Count("products")).filter(n__gt=0)               # por objeto; filter depois = HAVING
Category.objects.annotate(n=Count("products", distinct=True))                # distinct evita inflar com 2 JOINs
CartItem.objects.aggregate(t=Sum(F("quantity") * F("product__price")))["t"] # total no banco
Product.objects.values("category").annotate(n=Count("id"))                   # GROUP BY
```

## Criar, atualizar, apagar
```python
Product.objects.create(...)                              # INSERT (chama save())
obj, criado = Product.objects.get_or_create(sku="X", defaults={...})
obj, criado = Product.objects.update_or_create(sku="X", defaults={...})
Product.objects.bulk_create([...])                       # 1 INSERT; não chama save() nem sinais
obj.save(update_fields=["stock"])                        # só estas colunas
Product.objects.filter(...).update(is_active=False)      # 1 UPDATE; sem save(), sem auto_now
Product.objects.filter(...).delete()
```

## Transações e bloqueios
```python
from django.db import transaction

@transaction.atomic                                       # erro = ROLLBACK de tudo
def create_order(user): ...

with transaction.atomic():
    p = Product.objects.select_for_update().get(pk=1)     # trava a linha até o fim do bloco
    # várias linhas: sempre .order_by("pk") (evita deadlock)

transaction.on_commit(lambda: enviar_email())             # só depois do COMMIT
```

## Depurar consultas
```python
from django.db import connection
from django.test.utils import CaptureQueriesContext
with CaptureQueriesContext(connection) as ctx: ...
len(ctx), [q["sql"] for q in ctx.captured_queries]
print(qs.query)                                           # SQL gerado
qs.explain()                                              # EXPLAIN
# pytest-django: with django_assert_max_num_queries(5): ...
```

## Regras de bolso
- QuerySet é **lazy** e tem **cache**: `len(qs)` carrega tudo; use `count()`/`exists()`.
- Relação usada em laço → `select_related` (para um) ou `prefetch_related` (para muitos).
- Dinheiro em `DecimalField`; nunca `float`.
- Mudança de estoque/contador: `F()` ou `select_for_update()`, nunca ler-somar-gravar em Python.
- `update()`, `delete()` em lote e `bulk_create` **pulam** `save()`, sinais e `auto_now`.
- Restrições importantes ficam também no **banco** (`UniqueConstraint`, `CheckConstraint`).
