import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db
SENHA = "dev-somente-local-123"


def login(username):
    c = APIClient()
    if username:
        t = c.post("/api/v1/auth/token/", {"username": username, "password": SENHA}, format="json").json()["access"]
        c.credentials(HTTP_AUTHORIZATION="Bearer " + t)
    return c


@pytest.mark.parametrize(
    "quem,get,post",
    [
        (None, 200, 401),
        ("cliente", 200, 403),
        ("estoquista", 200, 403),
        ("gerente", 200, 201),
    ],
)
def test_matriz_do_catalogo(seed, quem, get, post):
    c = login(quem)
    assert c.get("/api/v1/products/").status_code == get
    novo = {"sku": "NEW-001", "name": "Novo", "price": "10.00", "stock": 1, "category_slug": "audio"}
    assert c.post("/api/v1/products/", novo, format="json").status_code == post


def test_rotas_privadas_sao_fechadas_por_padrao(seed):
    anon = login(None)
    for url in ["/api/v1/cart/", "/api/v1/orders/", "/api/v1/auth/me/"]:
        assert anon.get(url).status_code == 401


def test_so_o_dono_cancela(seed):
    cliente = login("cliente")
    cliente.post("/api/v1/cart/items/", {"product": 3, "quantity": 1}, format="json")
    oid = cliente.post("/api/v1/orders/").json()["id"]
    assert login("gerente").post(f"/api/v1/orders/{oid}/cancel/").status_code == 404  # fora do escopo
    assert cliente.post(f"/api/v1/orders/{oid}/cancel/").status_code == 200


RECURSOS = [
    ("GET", "/api/v1/products/"),
    ("GET", "/api/v1/categories/"),
    ("GET", "/api/v1/cart/"),
    ("GET", "/api/v1/orders/"),
    ("POST", "/api/v1/orders/"),
    ("GET", "/api/v1/auth/me/"),
]
PUBLICOS = {("GET", "/api/v1/products/"), ("GET", "/api/v1/categories/")}


@pytest.mark.parametrize("metodo,url", RECURSOS)
def test_anonimo_so_acessa_o_que_e_publico(seed, metodo, url):
    r = getattr(login(None), metodo.lower())(url)
    esperado_aberto = (metodo, url) in PUBLICOS
    assert (r.status_code != 401) == esperado_aberto
