"""Teste de CARACTERIZAÇÃO (golden master) do código legado: ele não diz o que o código DEVERIA fazer, mas o que ele FAZ HOJE.
Gravar:  GOLDEN=gravar uv run pytest tests/test_legado_caracterizacao.py      Conferir: uv run pytest tests/test_legado_caracterizacao.py
Só roda em SQLite: o legado usa SQL cru com datetime('now') (um motivo a mais para refatorar)."""
import itertools
import json
import os
import pathlib

import pytest
from django.db import connection

from apps.catalog.models import Category, Product
from legado import pedidos_legado

GOLDEN = pathlib.Path(__file__).parent / "golden" / "legado.json"
pytestmark = [pytest.mark.django_db, pytest.mark.skipif(connection.vendor != "sqlite", reason="legado usa SQL específico do SQLite")]

CARRINHOS = {
    "vazio": [],
    "barato": [{"sku": "A-100", "qtd": 1}],                          # total 100
    "medio": [{"sku": "A-100", "qtd": 3}],                           # total 300
    "caro": [{"sku": "B-300", "qtd": 2}],                            # total 600 (> 500: PROMO20 vale 20%)
    "misto": [{"sku": "A-100", "qtd": 2}, {"sku": "D-020", "qtd": 1}],
    "limite_frete": [{"sku": "A-100", "qtd": 2}],                    # total 200 EXATO (a fronteira do frete)
    "sku_inexistente": [{"sku": "ZZZ", "qtd": 1}],
    "inativo": [{"sku": "C-OFF", "qtd": 1}],
    "sem_estoque": [{"sku": "D-020", "qtd": 2}],
}
CUPONS = [None, "", "PROMO10", "PROMO20", "FRETEGRATIS", "XPTO"]
FORMAS = ["pix", "cartao", "boleto", "cheque", None]
CASOS = [(c, k, f) for c, k, f in itertools.product(CARRINHOS, CUPONS, FORMAS)]


@pytest.fixture
def mundo(django_user_model):
    cat = Category.objects.create(name="Geral", slug="geral")
    for sku, preco, estoque, ativo in [("A-100", "100.00", 10, True), ("B-300", "300.00", 5, True), ("C-OFF", "50.00", 5, False), ("D-020", "20.00", 1, True)]:
        Product.objects.create(category=cat, sku=sku, name=sku, price=preco, stock=estoque, is_active=ativo)
    return django_user_model.objects.create_user(username="legado", password="x" * 12)


def executar(user, carrinho, cupom, forma):
    dados = {"user_id": user.pk, "itens": [dict(i) for i in CARRINHOS[carrinho]], "cupom": cupom, "forma_pgto": forma}
    antes = pedidos_legado.TOTAL_PEDIDOS
    resp = pedidos_legado.processar_pedido(dados)
    resp = {k: (bool(v) if k == "pedido_id" else v) for k, v in resp.items()}      # o id depende do banco, não do comportamento
    estoque = dict(Product.objects.values_list("sku", "stock"))
    return {"resp": resp, "estoque": estoque, "contador": pedidos_legado.TOTAL_PEDIDOS - antes}


def test_gravar_ou_conferir_o_comportamento_atual(mundo, capsys):
    obtido = {}
    for caso in CASOS:
        # cada caso parte do mesmo estado: desfaz o que o anterior mexeu
        for sku, est in [("A-100", 10), ("B-300", 5), ("C-OFF", 5), ("D-020", 1)]:
            Product.objects.filter(sku=sku).update(stock=est)
        obtido["|".join(str(x) for x in caso)] = executar(mundo, *caso)
    capsys.readouterr()
    if os.environ.get("GOLDEN") == "gravar":
        GOLDEN.write_text(json.dumps(obtido, indent=1, sort_keys=True, ensure_ascii=False))
        pytest.skip(f"golden master gravado: {len(obtido)} casos")
    esperado = json.loads(GOLDEN.read_text())
    diferentes = [k for k in esperado if esperado[k] != obtido.get(k)]
    assert not diferentes, f"{len(diferentes)} caso(s) mudaram de comportamento, ex.: {diferentes[:3]}"
    assert set(esperado) == set(obtido)
