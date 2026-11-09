"""TESTE DE CONTRATO (princípio de Liskov): TODA implementação de PedidoRepository precisa se comportar igual."""

from decimal import Decimal

import pytest

from apps.cart import services as carrinho
from apps.catalog.models import Product
from apps.orders.domain import ItemCarrinho, ProdutoInfo
from apps.orders.repositories import DjangoPedidoRepository, MemoriaPedidoRepository


@pytest.fixture(params=["memoria", "django"])
def cenario(request, db, cliente):
    """Monta o MESMO cenário nos dois adaptadores: usuário com 2 unidades do produto 'INF-002' no carrinho."""
    p = Product.objects.get(sku="INF-002")
    Product.objects.filter(pk=p.pk).update(stock=5)
    if request.param == "django":
        carrinho.add_item(cliente, p.pk, 2)
        return DjangoPedidoRepository(), cliente, p.pk
    info = ProdutoInfo(p.pk, p.name, p.price, 5, True)
    return MemoriaPedidoRepository(carrinhos={cliente: [ItemCarrinho(p.pk, 2)]}, produtos={p.pk: info}), cliente, p.pk


def estoque(repo, pid):
    with repo.transacao():
        return repo.travar_produtos([pid])[pid].estoque


def test_itens_do_carrinho(cenario):
    repo, user, pid = cenario
    with repo.transacao():
        itens = repo.itens_do_carrinho(repo.travar_carrinho(user))
    assert itens == [ItemCarrinho(pid, 2)]


def test_travar_produtos_ignora_ids_inexistentes(cenario):
    repo, _, pid = cenario
    with repo.transacao():
        assert set(repo.travar_produtos([pid, 999_999])) == {pid}


def test_baixar_estoque_so_se_houver(cenario):
    repo, _, pid = cenario
    with repo.transacao():
        assert repo.baixar_estoque(pid, 5) is True  # exatamente o que há
        assert repo.baixar_estoque(pid, 1) is False  # acabou: recusa em vez de ficar negativo
    assert estoque(repo, pid) == 0


def test_pedido_criado_tem_o_total_dado(cenario):
    repo, user, pid = cenario
    with repo.transacao():
        carr = repo.travar_carrinho(user)
        itens = repo.itens_do_carrinho(carr)
        info = repo.travar_produtos([pid])[pid]
        from apps.orders.domain import montar_linhas, total

        linhas = montar_linhas(itens, {pid: info})
        pedido = repo.criar_pedido(user, linhas, total(linhas))
    assert pedido.total == info.preco * 2 and isinstance(pedido.total, Decimal)  # o contrato: o pedido criado expõe `.total`


def test_transacao_desfaz_o_que_foi_feito_se_der_erro(cenario):
    repo, _, pid = cenario
    with pytest.raises(RuntimeError), repo.transacao():
        assert repo.baixar_estoque(pid, 3)
        raise RuntimeError("falha no meio")
    assert estoque(repo, pid) == 5  # o rollback restaurou o estoque nos DOIS adaptadores
