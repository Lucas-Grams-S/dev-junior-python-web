"""Teste de contrato: o que a API devolve bate com o schema OpenAPI publicado?"""
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.django_db
SCHEMA = yaml.safe_load(Path("schema.yml").read_text())["components"]["schemas"]


def campos_do_schema(nome):
    return set(SCHEMA[nome]["properties"])


def test_produto_devolve_exatamente_os_campos_do_schema(api_as):
    item = api_as(None).get("/api/v1/products/").json()["results"][0]
    # category_slug é write_only: não aparece na leitura, e o schema de resposta também não o lista
    assert set(item) == campos_do_schema("Product") - {"category_slug"}


def test_pedido_devolve_exatamente_os_campos_do_schema(api_as):
    cli = api_as("cliente")
    cli.post("/api/v1/cart/items/", {"product": 2, "quantity": 1}, format="json")
    pedido = cli.post("/api/v1/orders/").json()
    assert set(pedido) == campos_do_schema("Order")
    assert set(pedido["items"][0]) == campos_do_schema("OrderItem")


def test_erro_segue_o_schema_error(api_as):
    erro = api_as("cliente").post("/api/v1/orders/").json()
    assert set(erro) == campos_do_schema("Error") == {"detail", "code"}
