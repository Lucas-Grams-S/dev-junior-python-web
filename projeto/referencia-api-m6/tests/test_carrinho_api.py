import pytest

from apps.catalog.models import Product

pytestmark = pytest.mark.django_db


@pytest.fixture
def cli(api_as):
    return api_as("cliente")


def adicionar(cli, produto, qtd=1):
    return cli.post("/api/v1/cart/items/", {"product": produto, "quantity": qtd}, format="json")


def test_adicionar_duas_vezes_soma_a_quantidade(cli):
    adicionar(cli, 2, 1)
    r = adicionar(cli, 2, 2)
    assert r.status_code == 201 and r.json()["quantity"] == 3


def test_produto_inativo_nao_entra(cli):
    inativo = Product.objects.filter(is_active=False).first()
    r = adicionar(cli, inativo.pk)
    assert r.status_code == 422 and r.json()["detail"] == "Produto indisponível."


def test_acima_do_estoque_da_422(cli):
    Product.objects.filter(pk=2).update(stock=3)
    assert adicionar(cli, 2, 4).status_code == 422


def test_alterar_quantidade_e_remover_com_zero(cli):
    item = adicionar(cli, 2, 1).json()["id"]
    assert cli.patch(f"/api/v1/cart/items/{item}/", {"quantity": 5}, format="json").json()["quantity"] == 5
    assert cli.patch(f"/api/v1/cart/items/{item}/", {"quantity": 0}, format="json").status_code == 204
    assert cli.get("/api/v1/cart/").json()["count"] == 0


def test_alterar_acima_do_estoque_da_422(cli):
    Product.objects.filter(pk=2).update(stock=2)
    item = adicionar(cli, 2, 1).json()["id"]
    assert cli.patch(f"/api/v1/cart/items/{item}/", {"quantity": 9}, format="json").status_code == 422


def test_remover_item(cli):
    item = adicionar(cli, 2, 1).json()["id"]
    assert cli.delete(f"/api/v1/cart/items/{item}/").status_code == 204


def test_item_de_outro_usuario_da_404(cli, api_as):
    item = adicionar(cli, 2, 1).json()["id"]
    outro = api_as("gerente")
    assert outro.patch(f"/api/v1/cart/items/{item}/", {"quantity": 1}, format="json").status_code == 404
    assert outro.delete(f"/api/v1/cart/items/{item}/").status_code == 404
