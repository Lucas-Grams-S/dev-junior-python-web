# 17. Pedidos com controle de estoque (transação)

> ⏱️ ~1h30 · Módulo 5 · Pré-requisitos: [06](06-orm-relacionamentos-agregacoes.md), [12](12-permissoes.md), [16](16-carrinho.md); transações e ACID ([aula 3.09](../03-banco-de-dados/09-transacoes-acid.md))

> ⚠️ **Nota de verificação.** Como nas aulas 12 a 16, o laboratório não estava disponível: os blocos **não foram executados** e as saídas em `text` são as esperadas. O teste de **concorrência** só faz sentido em **PostgreSQL** (no SQLite o `select_for_update()` é ignorado e o banco trava a escrita inteira); a aula mostra como rodá-lo com o Postgres do Docker (aula 3.03). Os nomes `Order`/`OrderItem` seguem o `projeto-central.md`.

## 🎯 Objetivos
Ao final desta aula você consegue:
- Modelar `Order` e `OrderItem` com **preço congelado** e restrições no banco
- Criar um pedido a partir do carrinho em **uma única transação** (`transaction.atomic`): ou tudo acontece, ou nada
- Explicar e evitar a **venda a mais** (*overselling*) com `select_for_update()` e atualização condicional
- Evitar *deadlock* ordenando os bloqueios e evitar pedido duplicado por duplo clique
- Cancelar um pedido devolvendo o estoque e testar rollback e concorrência

## 🤔 Por que isso importa
É aqui que o sistema mexe com **dinheiro e estoque** ao mesmo tempo. Dois clientes comprando a última unidade, um erro no meio do pedido que deixa o estoque baixado sem pedido criado, um duplo clique que cobra duas vezes: são bugs reais de e-commerce, difíceis de reproduzir e caros. Transação é o assunto de entrevista que separa quem decorou ORM de quem entende banco.

## 💡 Intuição (explicação simples)
Imagine o **caixa de uma loja com uma única unidade** de um produto e duas pessoas na fila, cada uma convencida de que vai levar. Sem regra, o caixa atende as duas “ao mesmo tempo” e vende o que não tem. A solução é **uma pessoa de cada vez no caixa** (bloqueio) e uma regra de ouro: *ou a venda inteira acontece (tira do estoque, emite a nota, esvazia o carrinho), ou nada acontece*. Se faltar um item no meio, tudo é desfeito, como se nunca tivesse começado.

## 🔬 Como funciona por dentro
```mermaid
sequenceDiagram
    participant U as Cliente
    participant V as View (POST)
    participant S as create_order()
    participant B as PostgreSQL
    U->>V: POST /pedidos/finalizar/
    V->>S: create_order(user)
    S->>B: BEGIN
    S->>B: SELECT … FROM cart FOR UPDATE (trava o carrinho)
    S->>B: SELECT … FROM product WHERE id IN (…) ORDER BY id FOR UPDATE
    S->>S: confere estoque de cada item
    alt falta estoque
        S->>B: ROLLBACK (nada muda)
        S-->>V: StockError
    else tudo certo
        S->>B: UPDATE product SET stock = stock - n
        S->>B: INSERT order, order_items (preço congelado)
        S->>B: DELETE cart_items
        S->>B: COMMIT
        S-->>V: Order
    end
```
- **Atomicidade.** `transaction.atomic()` abre uma transação; se uma exceção sair do bloco, o Django faz `ROLLBACK` de **tudo** que foi feito dentro. Estoque baixado + pedido criado + carrinho limpo andam juntos.
- **Venda a mais (*lost update*).** Sem bloqueio, duas requisições leem `stock = 1`, ambas concluem “tem estoque” e ambas gravam: vendeu 2 de 1. Um `if product.stock >= qty` seguido de `save()` **não** protege, porque entre o `if` e o `save` outra transação pode agir.
- **`select_for_update()`.** Gera `SELECT … FOR UPDATE`: as linhas lidas ficam **trancadas** até o fim da transação; a outra requisição espera, e quando liberar lê o estoque **já atualizado**. Só funciona **dentro de `atomic()`** e é ignorado pelo SQLite.
- **Atualização condicional (cinto e suspensório).** `UPDATE … SET stock = stock - n WHERE id = X AND stock >= n` é atômica por si só: se afetar 0 linhas, não havia estoque. Usamos junto com o bloqueio como defesa extra. Além disso, `PositiveIntegerField` cria `CHECK (stock >= 0)` no PostgreSQL: o banco recusa estoque negativo mesmo se o código errar.
- **Deadlock.** A pede o produto 1 e depois o 2; B pede o 2 e depois o 1: cada um segura o que o outro quer. A prevenção é **sempre travar na mesma ordem** (`ORDER BY id`). O PostgreSQL detecta e aborta uma das transações; ter uma ordem fixa quase elimina o problema.
- **Duplo clique.** Travar a **linha do carrinho** primeiro serializa as requisições do mesmo usuário: a segunda espera, encontra o carrinho vazio (a primeira o esvaziou) e falha com “carrinho vazio”. Não cria pedido duplicado.
- **Preço congelado.** `OrderItem.unit_price` copia `Product.price` no momento da compra; mudar o preço do produto depois **não altera** pedidos antigos.
- **`on_delete=PROTECT`.** Um produto vendido não pode ser apagado (e o usuário com pedidos também não): preserva o histórico. Para tirar do catálogo, desative (`is_active=False`).
- **Máquina de estados.** `pending → paid` e `pending → cancelled`. Cancelar só é permitido em `pending`. A tabela `Payment` entra no módulo 6/8; aqui o pedido nasce `pending`.

## 🛠️ Exemplo prático
**1. Models**
```python
# apps/orders/models.py
from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.catalog.models import Product


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        PAID = "paid", "Pago"
        CANCELLED = "cancelled", "Cancelado"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [models.CheckConstraint(condition=Q(total__gte=0), name="order_total_gte_0")]

    def __str__(self):
        return f"Pedido #{self.pk} ({self.get_status_display()})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="+")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField("preço unitário", max_digits=10, decimal_places=2)   # congelado na compra

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name="orderitem_quantity_gt_0"),
            models.UniqueConstraint(fields=["order", "product"], name="orderitem_unique_product"),
        ]

    @property
    def subtotal(self):
        return self.quantity * self.unit_price
```
```bash
uv run python manage.py startapp orders apps/orders     # name = "apps.orders" em apps.py; INSTALLED_APPS
uv run python manage.py makemigrations orders -n inicial
uv run python manage.py migrate
```
```text
Migrations for 'orders':
  apps/orders/migrations/0001_inicial.py
    + Create model Order
    + Create model OrderItem
    + Create constraint order_total_gte_0 on model order
    + Create constraint orderitem_quantity_gt_0 on model orderitem
    + Create constraint orderitem_unique_product on model orderitem
Operations to perform:
  Apply all migrations: accounts, admin, auth, cart, catalog, contenttypes, orders, sessions
Running migrations:
  Applying orders.0001_inicial... OK
```

**2. O serviço transacional (o coração da aula)**
```python
# apps/orders/services.py
import logging
from decimal import Decimal

from django.db import transaction
from django.db.models import F

from apps.cart.models import Cart
from apps.catalog.models import Product

from .models import Order, OrderItem

logger = logging.getLogger(__name__)


class OrderError(Exception):
    """Regra de negócio do pedido violada; a mensagem pode ser mostrada ao usuário."""


class EmptyCartError(OrderError):
    pass


class StockError(OrderError):
    pass


@transaction.atomic
def create_order(user):
    # 1) Trava o carrinho do usuário: serializa duplo clique / duas abas
    try:
        cart = Cart.objects.select_for_update().get(user=user)
    except Cart.DoesNotExist:
        raise EmptyCartError("Seu carrinho está vazio.") from None

    itens = list(cart.items.all())                                   # (product_id, quantity)
    if not itens:
        raise EmptyCartError("Seu carrinho está vazio.")

    # 2) Trava os produtos SEMPRE na mesma ordem (id): evita deadlock entre pedidos
    ids = sorted(i.product_id for i in itens)
    produtos = {p.pk: p for p in Product.objects.select_for_update().filter(pk__in=ids).order_by("pk")}

    # 3) Valida tudo ANTES de alterar qualquer coisa (mensagem completa para o usuário)
    problemas = []
    for item in itens:
        p = produtos.get(item.product_id)
        if p is None or not p.is_active:
            problemas.append(f"{p.name if p else 'Um produto'} não está mais disponível.")
        elif item.quantity > p.stock:
            problemas.append(f"{p.name}: restam {p.stock}, você pediu {item.quantity}.")
    if problemas:
        raise StockError(" ".join(problemas))                        # sai do atomic → ROLLBACK

    # 4) Cria o pedido com preço congelado e baixa o estoque
    total = Decimal("0")
    order = Order.objects.create(user=user, total=0)
    for item in itens:
        p = produtos[item.product_id]
        OrderItem.objects.create(order=order, product=p, quantity=item.quantity, unit_price=p.price)
        total += item.quantity * p.price
        baixou = Product.objects.filter(pk=p.pk, stock__gte=item.quantity).update(stock=F("stock") - item.quantity)
        if baixou != 1:                                              # defesa extra: nunca deveria ocorrer com o bloqueio
            raise StockError(f"{p.name}: o estoque mudou, tente novamente.")
    order.total = total
    order.save(update_fields=["total"])

    # 5) Esvazia o carrinho; tudo isto acontece junto, ou nada acontece
    cart.items.all().delete()
    logger.info("order_created order=%s user=%s total=%s items=%s", order.pk, user.pk, total, len(itens))
    return order


@transaction.atomic
def cancel_order(user, order_id):
    try:
        order = Order.objects.select_for_update().get(pk=order_id, user=user)       # só o dono cancela o seu
    except Order.DoesNotExist:
        raise OrderError("Pedido não encontrado.") from None
    if order.status != Order.Status.PENDING:
        raise OrderError("Só é possível cancelar pedidos pendentes.")

    itens = list(order.items.all())
    for item in sorted(itens, key=lambda i: i.product_id):                          # mesma ordem de bloqueio
        Product.objects.filter(pk=item.product_id).update(stock=F("stock") + item.quantity)
    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status"])
    logger.info("order_cancelled order=%s user=%s", order.pk, user.pk)
    return order
```
Pontos que valem uma segunda leitura:
- A **validação vem antes de qualquer escrita**, mas o `raise` dentro do `atomic` garante o `ROLLBACK` mesmo se algo falhasse depois.
- `select_for_update()` está dentro do `@transaction.atomic`: fora dele o Django levanta `TransactionManagementError`.
- Erros esperados (estoque, carrinho vazio) são **exceções de negócio**; a view os traduz em mensagens. Erros inesperados continuam subindo (viram 500 e aparecem no log, aula 14).
- Em `cancel_order`, o filtro por `user` impede cancelar o pedido alheio (aula 12).

**3. Views, URLs e templates**
```python
# apps/orders/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.cart.services import get_cart

from . import services
from .models import Order


@login_required
def checkout(request):
    """GET: resumo para conferir. O pedido só é criado no POST."""
    cart = get_cart(request.user)
    items = cart.items.select_related("product").order_by("product__name")
    if not items:
        messages.info(request, "Seu carrinho está vazio.")
        return redirect("cart:detail")
    return render(request, "orders/checkout.html", {"items": items, "total": cart.total()})


@login_required
@require_POST
def place(request):
    try:
        order = services.create_order(request.user)
    except services.OrderError as e:
        messages.error(request, str(e))
        return redirect("cart:detail")
    messages.success(request, f"Pedido #{order.pk} criado!")
    return redirect("orders:detail", pk=order.pk)                   # Post/Redirect/Get: F5 não duplica


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, "orders/list.html", {"orders": orders})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.filter(user=request.user).prefetch_related("items__product"), pk=pk)   # alheio → 404
    return render(request, "orders/detail.html", {"order": order})


@login_required
@require_POST
def cancel(request, pk):
    try:
        services.cancel_order(request.user, pk)
        messages.success(request, "Pedido cancelado e estoque devolvido.")
    except services.OrderError as e:
        messages.error(request, str(e))
    return redirect("orders:detail", pk=pk)
```
```python
# apps/orders/urls.py
from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("", views.order_list, name="list"),
    path("finalizar/", views.checkout, name="checkout"),
    path("finalizar/confirmar/", views.place, name="place"),
    path("<int:pk>/", views.order_detail, name="detail"),
    path("<int:pk>/cancelar/", views.cancel, name="cancel"),
]
# config/urls.py: path("pedidos/", include("apps.orders.urls")),
```
```html
{# orders/checkout.html #}
{% extends "base.html" %}
{% block conteudo %}
  <h1>Confirmar pedido</h1>
  <ul>{% for i in items %}<li>{{ i.quantity }} × {{ i.product.name }}: R$ {{ i.subtotal }}</li>{% endfor %}</ul>
  <p><strong>Total: R$ {{ total }}</strong></p>
  <form method="post" action="{% url 'orders:place' %}">{% csrf_token %}
    <button class="botao" type="submit">Finalizar pedido</button>
  </form>
{% endblock %}
```
```html
{# orders/detail.html #}
{% extends "base.html" %}
{% block conteudo %}
  <h1>Pedido #{{ order.pk }}</h1>
  <p>Status: <strong>{{ order.get_status_display }}</strong> · {{ order.created_at|date:"d/m/Y H:i" }}</p>
  <table>
    <thead><tr><th>Produto</th><th>Qtd</th><th>Preço</th><th>Subtotal</th></tr></thead>
    <tbody>{% for i in order.items.all %}
      <tr><td>{{ i.product.name }}</td><td>{{ i.quantity }}</td><td>R$ {{ i.unit_price }}</td><td>R$ {{ i.subtotal }}</td></tr>
    {% endfor %}</tbody>
    <tfoot><tr><th colspan="3">Total</th><th>R$ {{ order.total }}</th></tr></tfoot>
  </table>
  {% if order.status == "pending" %}
    <form method="post" action="{% url 'orders:cancel' order.pk %}">{% csrf_token %}<button type="submit">Cancelar pedido</button></form>
  {% endif %}
{% endblock %}
```
Na tela do carrinho (aula 16) acrescente um link “Finalizar compra” para `orders:checkout`; `orders/list.html` é uma tabela simples de `orders` com link para o detalhe.

**4. Testes de regra, rollback e segurança**
```python
import pytest
from decimal import Decimal
from django.db import IntegrityError, transaction
from django.urls import reverse

from apps.cart import services as carrinho
from apps.cart.models import CartItem
from apps.catalog.models import Category, Product
from apps.orders import services
from apps.orders.models import Order, OrderItem

pytestmark = pytest.mark.django_db
SENHA = "uma-senha-bem-forte-42"


@pytest.fixture
def ana(django_user_model):
    return django_user_model.objects.create_user("ana", "ana@exemplo.com", SENHA)


@pytest.fixture
def bia(django_user_model):
    return django_user_model.objects.create_user("bia", "bia@exemplo.com", SENHA)


@pytest.fixture
def mouse():
    cat = Category.objects.create(name="Periféricos", slug="perifericos")
    return Product.objects.create(category=cat, sku="MOU-1", name="Mouse", price=Decimal("59.90"), stock=5)


@pytest.fixture
def teclado(mouse):
    return Product.objects.create(category=mouse.category, sku="TEC-1", name="Teclado", price=Decimal("120.50"), stock=2)


def test_pedido_baixa_estoque_limpa_carrinho_e_congela_preco(ana, mouse, teclado):
    carrinho.add_item(ana, mouse.pk, 3)
    carrinho.add_item(ana, teclado.pk, 1)
    pedido = services.create_order(ana)
    assert pedido.total == Decimal("300.20") and pedido.status == "pending"
    mouse.refresh_from_db(), teclado.refresh_from_db()
    assert (mouse.stock, teclado.stock) == (2, 1)
    assert not CartItem.objects.filter(cart__user=ana).exists()
    mouse.price = Decimal("1.00")
    mouse.save()                                                       # preço muda depois...
    assert pedido.items.get(product=mouse).unit_price == Decimal("59.90")   # ...pedido não


def test_sem_estoque_nada_e_gravado_rollback(ana, mouse, teclado):
    carrinho.add_item(ana, mouse.pk, 2)
    carrinho.add_item(ana, teclado.pk, 2)
    Product.objects.filter(pk=teclado.pk).update(stock=1)             # alguém comprou antes
    with pytest.raises(services.StockError, match="Teclado"):
        services.create_order(ana)
    mouse.refresh_from_db()
    assert mouse.stock == 5                                           # o mouse NÃO foi baixado
    assert Order.objects.count() == 0 and OrderItem.objects.count() == 0
    assert CartItem.objects.filter(cart__user=ana).count() == 2       # carrinho intacto


def test_erro_no_meio_desfaz_tudo(ana, mouse, teclado, monkeypatch):
    carrinho.add_item(ana, mouse.pk, 1)
    carrinho.add_item(ana, teclado.pk, 1)
    original = OrderItem.objects.create
    chamadas = {"n": 0}

    def quebra_no_segundo(*args, **kwargs):
        chamadas["n"] += 1
        if chamadas["n"] == 2:
            raise RuntimeError("falha simulada")
        return original(*args, **kwargs)

    monkeypatch.setattr(OrderItem.objects, "create", quebra_no_segundo)
    with pytest.raises(RuntimeError):
        services.create_order(ana)
    mouse.refresh_from_db(), teclado.refresh_from_db()
    assert (mouse.stock, teclado.stock) == (5, 2) and Order.objects.count() == 0


def test_carrinho_vazio(ana):
    with pytest.raises(services.EmptyCartError):
        services.create_order(ana)


def test_duplo_envio_nao_cria_dois_pedidos(ana, mouse):
    carrinho.add_item(ana, mouse.pk, 1)
    services.create_order(ana)
    with pytest.raises(services.EmptyCartError):                      # a "segunda requisição" encontra o carrinho vazio
        services.create_order(ana)
    assert Order.objects.count() == 1


def test_produto_desativado_no_meio_bloqueia(ana, mouse):
    carrinho.add_item(ana, mouse.pk, 1)
    Product.objects.filter(pk=mouse.pk).update(is_active=False)
    with pytest.raises(services.StockError, match="disponível"):
        services.create_order(ana)


def test_cancelar_devolve_estoque_e_so_uma_vez(ana, mouse):
    carrinho.add_item(ana, mouse.pk, 2)
    pedido = services.create_order(ana)
    mouse.refresh_from_db()
    assert mouse.stock == 3
    services.cancel_order(ana, pedido.pk)
    mouse.refresh_from_db()
    assert mouse.stock == 5
    with pytest.raises(services.OrderError):
        services.cancel_order(ana, pedido.pk)                         # não devolve duas vezes
    mouse.refresh_from_db()
    assert mouse.stock == 5


def test_nao_cancela_pedido_alheio(ana, bia, mouse):
    carrinho.add_item(ana, mouse.pk, 1)
    pedido = services.create_order(ana)
    with pytest.raises(services.OrderError):
        services.cancel_order(bia, pedido.pk)


def test_banco_recusa_estoque_negativo(mouse):
    with pytest.raises(IntegrityError), transaction.atomic():
        Product.objects.filter(pk=mouse.pk).update(stock=-1)


def test_finalizar_so_por_post_e_exige_login(client, ana, mouse):
    assert client.post(reverse("orders:place")).status_code == 302          # anônimo → login
    client.force_login(ana)
    carrinho.add_item(ana, mouse.pk, 1)
    assert client.get(reverse("orders:place")).status_code == 405
    r = client.post(reverse("orders:place"))
    pedido = Order.objects.get()
    assert r.status_code == 302 and r.url == reverse("orders:detail", args=[pedido.pk])


def test_pedido_alheio_da_404(client, ana, bia, mouse):
    carrinho.add_item(ana, mouse.pk, 1)
    pedido = services.create_order(ana)
    client.force_login(bia)
    assert client.get(reverse("orders:detail", args=[pedido.pk])).status_code == 404


def test_detalhe_do_pedido_nao_faz_n_mais_1(client, ana, mouse, teclado, django_assert_max_num_queries):
    carrinho.add_item(ana, mouse.pk, 1)
    carrinho.add_item(ana, teclado.pk, 1)
    pedido = services.create_order(ana)
    client.force_login(ana)
    with django_assert_max_num_queries(8):
        assert client.get(reverse("orders:detail", args=[pedido.pk])).status_code == 200
```
```bash
uv run python manage.py check
uv run pytest apps/orders apps/cart -q
```
```text
System check identified no issues (0 silenced).
.......................................................................... [100%]
```
O teste `test_erro_no_meio_desfaz_tudo` é o mais didático: força uma falha **depois** de o estoque do primeiro produto ter sido baixado e mostra que, ao final, nada mudou. Sem `atomic`, o mouse ficaria com estoque 4 e nenhum pedido.

**5. Teste de concorrência (PostgreSQL)**
```bash
docker run -d --name pg-minishop-teste -e POSTGRES_PASSWORD=teste -e POSTGRES_DB=minishop_teste -p 5433:5432 postgres:18
DATABASE_URL=postgres://postgres:teste@127.0.0.1:5433/minishop_teste uv run pytest apps/orders/tests/test_concorrencia.py -q
docker rm -f pg-minishop-teste
```
```python
# apps/orders/tests/test_concorrencia.py
from concurrent.futures import ThreadPoolExecutor

import pytest
from decimal import Decimal
from django.db import connection

from apps.cart import services as carrinho
from apps.catalog.models import Category, Product
from apps.orders import services
from apps.orders.models import Order

pytestmark = [
    pytest.mark.django_db(transaction=True),             # commits reais: as threads precisam enxergar os dados
    pytest.mark.skipif(connection.vendor != "postgresql", reason="select_for_update exige PostgreSQL"),
]


def test_ultima_unidade_so_vende_uma_vez(django_user_model):
    cat = Category.objects.create(name="C", slug="c")
    produto = Product.objects.create(category=cat, sku="UNICO-1", name="Última unidade", price=Decimal("10.00"), stock=1)
    usuarios = [django_user_model.objects.create_user(f"u{i}", f"u{i}@x.com", "senha-forte-12345") for i in range(8)]
    for u in usuarios:
        carrinho.add_item(u, produto.pk, 1)               # todos têm 1 unidade no carrinho: só uma existe

    def comprar(u):
        try:
            services.create_order(u)
            return "ok"
        except services.StockError:
            return "sem estoque"
        finally:
            connection.close()                            # cada thread tem a própria conexão

    with ThreadPoolExecutor(max_workers=8) as pool:
        resultados = list(pool.map(comprar, usuarios))

    produto.refresh_from_db()
    assert resultados.count("ok") == 1 and resultados.count("sem estoque") == 7
    assert produto.stock == 0 and Order.objects.count() == 1
```
```text
.                                                                        [100%]
```
Para ver o bug que a aula evita, remova temporariamente `.select_for_update()` e a condição `stock__gte` do `update`: o teste passará a falhar de forma intermitente (mais de um `ok`, ou erro de `CHECK`). Falhas **intermitentes** são a assinatura dos bugs de concorrência. Em CI (módulo 12) use um serviço PostgreSQL e rode este arquivo.

## 🧠 Pausa para lógica
**Problema (tudo ou nada).** Implemente `aplicar_pedidos(estoque, pedidos)` em Python puro. `estoque` é um dicionário `{sku: qtd}` e cada pedido é uma lista `[(sku, qtd), …]`. Cada pedido deve ser **atômico**: se qualquer item faltar, nenhum item do pedido é baixado. Devolva o estoque final e a lista de pedidos aceitos/recusados, na ordem de chegada.

<details><summary>Dica</summary>
Trabalhe numa <strong>cópia</strong> do estoque para cada pedido e só a adote (<em>commit</em>) se todos os itens couberem; descartar a cópia é o <em>rollback</em>. Cuidado com o mesmo SKU repetido no pedido.
</details>

<details><summary>Solução comentada</summary>

```python
from collections import Counter


def aplicar_pedidos(estoque, pedidos):
    estoque = dict(estoque)
    resultado = []
    for numero, itens in enumerate(pedidos, start=1):
        necessario = Counter()
        for sku, qtd in itens:                        # soma SKUs repetidos antes de comparar
            necessario[sku] += qtd
        if all(estoque.get(sku, 0) >= qtd for sku, qtd in necessario.items()):
            for sku, qtd in necessario.items():       # "commit": só agora o estoque muda
                estoque[sku] -= qtd
            resultado.append((numero, "aceito"))
        else:
            resultado.append((numero, "recusado"))    # "rollback": nada foi alterado
    return estoque, resultado


estoque = {"A": 2, "B": 1}
pedidos = [[("A", 1), ("B", 1)], [("A", 1), ("B", 1)], [("A", 1)], [("A", 1), ("A", 1)]]
print(aplicar_pedidos(estoque, pedidos))
```
```text
({'A': 0, 'B': 0}, [(1, 'aceito'), (2, 'recusado'), (3, 'aceito'), (4, 'recusado')])
```
O pedido 2 falhou por causa do `B`, e **o `A` dele não foi baixado**: por isso o pedido 3 ainda conseguiu o `A`. É exatamente o que o `atomic()` garante no banco.
</details>

## ⚠️ Erros comuns e boas práticas
| Mensagem / sintoma | Causa | Solução |
|---|---|---|
| `TransactionManagementError: select_for_update cannot be used outside of a transaction` | `select_for_update()` sem `atomic()` | Decore a função com `@transaction.atomic` |
| Estoque negativo ou vendido a mais | `if estoque >= n: estoque -= n; save()` sem bloqueio | `select_for_update()` + `update` condicional |
| `deadlock detected` (PostgreSQL) | Bloqueios em ordens diferentes | Sempre `order_by("pk")` ao travar vários |
| Pedido duplicado ao clicar duas vezes | Nenhuma serialização por usuário | Trave o carrinho primeiro; PRG; botão desabilita no envio |
| Pedido criado mas estoque não baixou | Passos fora de uma transação | Tudo dentro de um único `atomic` |
| `ProtectedError: Cannot delete some instances of model 'Product'` | Produto já vendido (`PROTECT`) | Desative (`is_active=False`) |
| `IntegrityError … stock >= 0` | `CHECK` do PostgreSQL pegou o erro do código | Corrija a regra; o banco foi a última defesa |
| Teste de concorrência passa “às vezes” | Rodou em SQLite ou sem `transaction=True` | PostgreSQL e `django_db(transaction=True)` |
| `except Exception: pass` dentro do `atomic` | Engole o erro e o Django comita pela metade | Deixe a exceção sair do bloco, ou use `atomic` aninhado (savepoint) |

- Mantenha as transações **curtas**: nada de chamada HTTP externa (gateway de pagamento, e-mail) dentro do `atomic`. Faça-as **depois** do `commit` (`transaction.on_commit`).
- Valide **antes** de gravar e dê mensagens completas ao usuário.
- Dinheiro em `Decimal`; preço copiado para o item; histórico protegido por `PROTECT`.
- Registre (`logger.info`) os eventos de negócio importantes: pedido criado e cancelado.
- `ATOMIC_REQUESTS = True` envolve cada requisição numa transação, mas esconde o tamanho real dela; preferimos `atomic` explícito no serviço.

## 🧩 Exercícios
**1. Fixação**
(a) O que o `ROLLBACK` desfaz quando falta estoque do segundo item? (b) Por que `if p.stock >= n: p.stock -= n; p.save()` não é seguro? (c) Para que serve ordenar os bloqueios por `id`? (d) Por que copiar o preço para o `OrderItem`?

<details><summary>Solução</summary>

(a) Tudo o que a transação fez: baixa de estoque do primeiro item, pedido e itens criados. (b) Entre o `if` e o `save` outra transação pode alterar o estoque; as duas passam pelo `if` e vendem a mais. (c) Evita *deadlock*: todas as transações pedem as linhas na mesma ordem. (d) O preço do catálogo muda; o pedido precisa registrar o que foi cobrado.
</details>

**2. Aplicação no projeto MiniShop**
Entregue o pedido transacional.

Critérios de pronto:
- [ ] App `orders` com `Order`, `OrderItem`, restrições no banco e migração
- [ ] `create_order` e `cancel_order` em `services.py`, dentro de `atomic`, com bloqueios ordenados
- [ ] Fluxo: carrinho → resumo (GET) → confirmar (POST) → detalhe, com *Post/Redirect/Get*
- [ ] “Meus pedidos” e detalhe visíveis só ao dono (404 para pedido alheio)
- [ ] Teste de rollback (falta estoque e falha no meio), duplo envio, cancelamento e preço congelado
- [ ] Teste de concorrência em PostgreSQL (uma unidade, vários compradores) rodando localmente
- [ ] Pedidos registrados no Admin **somente leitura** (sem adicionar/excluir) com `OrderItem` em *inline*
- [ ] Commit `feat(orders): transactional checkout with stock control`

<details><summary>Solução de referência (Admin somente leitura)</summary>

```python
# apps/orders/admin.py
from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ["product", "quantity", "unit_price"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "status", "total", "created_at"]
    list_filter = ["status"]
    list_select_related = ["user"]
    readonly_fields = ["user", "total", "created_at"]
    inlines = [OrderItemInline]

    def has_add_permission(self, request):
        return False                                     # pedidos nascem pelo checkout, não pelo Admin

    def has_delete_permission(self, request, obj=None):
        return False                                     # histórico não se apaga; cancela-se pelo serviço
```
Alterar o `status` pelo Admin **não devolve o estoque**: o motivo de preferir ações que chamam `cancel_order`. Deixe o campo `status` como `readonly` se quiser impedir o atalho.
</details>

**3. Desafio (opcional)**
Aceite uma `Idempotency-Key` (um UUID gerado no formulário de checkout) e guarde-a em uma coluna `UNIQUE` do `Order`. Reenvios com a mesma chave devolvem o **mesmo pedido** em vez de erro. Depois, use `transaction.on_commit` para enviar um e-mail de confirmação **somente após** o commit, e teste que um pedido que falha por estoque **não** envia e-mail.

## 🎤 Na entrevista
- **Como evitar vender mais do que existe em estoque?** Dentro de uma transação, travar as linhas dos produtos com `select_for_update()` (na mesma ordem) e baixar o estoque com `UPDATE … WHERE stock >= n`; mais uma restrição `CHECK (stock >= 0)` no banco como última defesa.
- **O que é atomicidade e como o Django a garante?** Um conjunto de operações acontece por inteiro ou não acontece. `transaction.atomic()` abre a transação e faz `ROLLBACK` se uma exceção sair do bloco.
- **O que é deadlock e como evitar?** Duas transações esperando uma pela outra por travas em ordem inversa. Travar sempre na mesma ordem, manter transações curtas e tratar o erro de deadlock com nova tentativa.
- **Por que guardar o preço no item do pedido?** O preço do produto muda; o pedido é um registro histórico do que foi cobrado.

## 📚 Para ir além
- 📄 Documentação oficial: [Transações de banco no Django](https://docs.djangoproject.com/en/5.2/topics/db/transactions/). `atomic`, `on_commit`, savepoints.
- 📄 Documentação oficial: [`select_for_update()`](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update). Opções `nowait`, `skip_locked`, `of`.
- 📄 Documentação oficial: [PostgreSQL — bloqueios explícitos](https://www.postgresql.org/docs/current/explicit-locking.html). Como `FOR UPDATE` funciona por baixo.
- 📄 Documentação oficial: [pytest-django — transações nos testes](https://pytest-django.readthedocs.io/en/latest/helpers.html#pytest-mark-django-db-request-database-access). `transaction=True`.
- 📑 Artigo/tutorial: [Django ORM Cookbook — transações](https://books.agiliq.com/projects/django-orm-cookbook/en/latest/). Exemplos curtos.
- 🏋️ Prática extra: reproduza um deadlock de propósito com dois terminais `psql` e leia a mensagem do PostgreSQL.

> Links verificados em 2026-11-08 (HTTP 200).

## ✅ Checklist da aula
- [ ] Pedido, itens, baixa de estoque e limpeza do carrinho numa única transação
- [ ] Bloqueio do carrinho e dos produtos, em ordem fixa
- [ ] Preço congelado em `OrderItem.unit_price`
- [ ] Cancelamento devolve estoque uma única vez
- [ ] Testes de rollback, duplo envio e concorrência (PostgreSQL)
