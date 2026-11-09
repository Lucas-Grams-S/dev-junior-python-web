"""Matriz de autorização: PAPEL x AÇÃO x DONO. A tabela abaixo é a POLÍTICA escrita à mão; o teste confere o código contra ela."""
import pytest
from django.contrib.auth.models import Group, Permission
from django.test import Client

from apps.cart import services as carrinho
from apps.catalog.models import Product
from apps.orders import services as pedidos

pytestmark = pytest.mark.django_db
SENHA = "dev-somente-local-123"

# ator -> (código por ação). Ações sobre um pedido e um item de carrinho do DONO ("cliente").
POLITICA = {
    #                ver_pedido, cancelar, pagar, mexer_no_item_alheio, criar_produto, apagar_produto
    "anonimo":     (401, 401, 401, 401, 401, 401),
    "dono":        (200, 200, 201, 200, 403, 403),    # pagar cria a cobrança (201); mexer no PRÓPRIO item é permitido
    "outro":       (404, 404, 404, 404, 403, 403),    # recurso alheio "não existe" para ele
    "estoquista":  (404, 404, 404, 404, 403, 403),    # papel de catálogo: NÃO tem acesso a pedidos alheios (menor privilégio)
    "gerente":     (404, 404, 404, 404, 201, 409),    # gerencia catálogo; produto já vendido não pode ser apagado (409)
    "atendimento": (200, 403, 404, 404, 403, 403),    # tem `orders.view_order`: VÊ todos os pedidos, mas não cancela nem paga por ninguém
}


def cliente_http(user):
    if user is None:
        return Client()
    r = Client().post("/api/v1/auth/token/", {"username": user, "password": SENHA}, content_type="application/json")
    return Client(HTTP_AUTHORIZATION="Bearer " + r.json()["access"])


@pytest.fixture
def cenario(seed, django_user_model, settings):
    settings.ORDER_EMAIL_MODE = "off"
    dono = django_user_model.objects.get(username="cliente")
    django_user_model.objects.create_user(username="outro", password=SENHA)
    atend = django_user_model.objects.create_user(username="atendimento", password=SENHA)
    grupo, _ = Group.objects.get_or_create(name="Atendimento")
    grupo.permissions.add(Permission.objects.get(codename="view_order", content_type__app_label="orders"))
    atend.groups.add(grupo)
    produto = Product.objects.filter(is_active=True, stock__gt=5).first()
    carrinho.add_item(dono, produto.pk, 1)
    item_id = dono.cart.items.first().pk
    pedido = pedidos.create_order(dono)
    carrinho.add_item(dono, produto.pk, 1)             # recria um item (o carrinho esvaziou ao criar o pedido)
    return {"pedido": pedido.pk, "item": dono.cart.items.first().pk, "produto": produto.pk}


def usuario_do_ator(ator):
    return {"anonimo": None, "dono": "cliente", "outro": "outro", "estoquista": "estoquista", "gerente": "gerente", "atendimento": "atendimento"}[ator]


@pytest.mark.parametrize("ator", POLITICA)
def test_ver_pedido(cenario, ator):
    r = cliente_http(usuario_do_ator(ator)).get(f"/api/v1/orders/{cenario['pedido']}/")
    assert r.status_code == POLITICA[ator][0]


@pytest.mark.parametrize("ator", POLITICA)
def test_cancelar_pedido(cenario, ator):
    r = cliente_http(usuario_do_ator(ator)).post(f"/api/v1/orders/{cenario['pedido']}/cancel/")
    assert r.status_code == POLITICA[ator][1]


@pytest.mark.parametrize("ator", POLITICA)
def test_pagar_pedido(cenario, ator):
    r = cliente_http(usuario_do_ator(ator)).post(f"/api/v1/orders/{cenario['pedido']}/pay/")
    assert r.status_code == POLITICA[ator][2]


@pytest.mark.parametrize("ator", POLITICA)
def test_alterar_item_do_carrinho_alheio(cenario, ator):
    r = cliente_http(usuario_do_ator(ator)).patch(f"/api/v1/cart/items/{cenario['item']}/", {"quantity": 2}, content_type="application/json")
    assert r.status_code == POLITICA[ator][3]


@pytest.mark.parametrize("ator", POLITICA)
def test_criar_produto(cenario, ator):
    corpo = {"sku": "TST-901", "name": "Novo", "price": "9.90", "stock": 1, "category_slug": Product.objects.first().category.slug}
    r = cliente_http(usuario_do_ator(ator)).post("/api/v1/products/", corpo, content_type="application/json")
    assert r.status_code == POLITICA[ator][4]


@pytest.mark.parametrize("ator", POLITICA)
def test_apagar_produto(cenario, ator):
    r = cliente_http(usuario_do_ator(ator)).delete(f"/api/v1/products/{cenario['produto']}/")
    assert r.status_code == POLITICA[ator][5]


def test_lista_de_pedidos_nunca_mostra_o_de_outro(cenario):
    corpo = cliente_http("outro").get("/api/v1/orders/").json()
    assert corpo["results"] == []


def test_gerente_apaga_produto_que_nunca_foi_vendido(cenario):
    livre = Product.objects.exclude(pk=cenario["produto"]).first()
    assert cliente_http("gerente").delete(f"/api/v1/products/{livre.pk}/").status_code == 204


def test_conflito_ao_apagar_produto_vendido_tem_corpo_padronizado(cenario):
    r = cliente_http("gerente").delete(f"/api/v1/products/{cenario['produto']}/")
    assert r.status_code == 409 and r.json()["code"] == "in_use"
