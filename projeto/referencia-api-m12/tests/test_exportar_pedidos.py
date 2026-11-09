import pytest

pytestmark = pytest.mark.django_db


def test_exporta_csv_com_cabecalho(api_as):
    r = api_as("cliente").get("/api/v1/orders/export/")
    assert r.status_code == 200
    assert r["Content-Type"].startswith("text/csv")
    assert r.content.decode().splitlines()[0] == "id,cliente,email,total,status"


# --- testes escritos pelo REVISOR para provar os comentários da revisão ------------------------------------------
import csv  # noqa: E402
import io  # noqa: E402

from django.db import connection  # noqa: E402
from django.test.utils import CaptureQueriesContext  # noqa: E402

from apps.cart import services as carrinho  # noqa: E402
from apps.orders import services as pedidos  # noqa: E402


@pytest.fixture
def pedidos_de_duas_pessoas(cliente, criar_usuario, criar_produto, settings):
    settings.ORDER_EMAIL_MODE = "off"
    outro = criar_usuario("+cmd")  # nome de usuário legítimo para o Django e perigoso numa planilha
    p = criar_produto(estoque=50)
    for u in (cliente, outro, outro, outro):
        carrinho.add_item(u, p.pk, 1)
        pedidos.create_order(u)
    return cliente, outro


def linhas_csv(resposta):
    return list(csv.reader(io.StringIO(resposta.content.decode())))


def test_anonimo_nao_exporta(api_anonimo):
    assert api_anonimo.get("/api/v1/orders/export/").status_code == 401


def test_o_csv_so_traz_os_pedidos_do_proprio_usuario(api_as, pedidos_de_duas_pessoas):  # comentário 1 (bloqueante)
    linhas = linhas_csv(api_as("cliente").get("/api/v1/orders/export/"))
    assert {linha[1] for linha in linhas[1:]} == {"cliente"} and len(linhas) == 2  # cabeçalho + 1 pedido


def test_celulas_de_texto_nao_viram_formulas_na_planilha(api_as, pedidos_de_duas_pessoas):  # comentário 2 (bloqueante)
    _cliente, outro = pedidos_de_duas_pessoas
    outro.set_password("dev-somente-local-123")
    outro.save()
    linhas = linhas_csv(api_as("+cmd").get("/api/v1/orders/export/"))
    textos = [celula for linha in linhas[1:] for celula in linha[1:3]]
    assert all(not t.startswith(("=", "+", "-", "@")) for t in textos), textos


def consultas_da_exportacao(api):
    with CaptureQueriesContext(connection) as ctx:
        api.get("/api/v1/orders/export/")
    return len(ctx)


def test_o_numero_de_consultas_nao_cresce_com_o_numero_de_pedidos(api_as, pedidos_de_duas_pessoas, criar_produto):  # comentário 3
    _cliente, outro = pedidos_de_duas_pessoas
    outro.set_password("dev-somente-local-123")
    outro.save()
    api = api_as("+cmd")
    com_3_pedidos = consultas_da_exportacao(api)
    produto = criar_produto(estoque=50)
    for _ in range(5):  # mais cinco pedidos do mesmo usuário
        carrinho.add_item(outro, produto.pk, 1)
        pedidos.create_order(outro)
    com_8_pedidos = consultas_da_exportacao(api)
    assert com_8_pedidos == com_3_pedidos, f"{com_3_pedidos} consultas com 3 pedidos, {com_8_pedidos} com 8: há consulta por pedido (N+1)"
