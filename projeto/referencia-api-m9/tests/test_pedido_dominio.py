"""Regras do pedido SEM banco: Python puro. Rodam em microssegundos."""
from decimal import Decimal

import pytest

from apps.orders import domain
from apps.orders.domain import ItemCarrinho, ProdutoInfo
from apps.orders.repositories import MemoriaPedidoRepository
from apps.orders.services import EmptyCartError, StockError, create_order


def produto(pid=1, nome="Mouse", preco="59.90", estoque=5, ativo=True):
    return ProdutoInfo(pid, nome, Decimal(preco), estoque, ativo)


# ------------------------------------------------------------------ domínio puro
def test_total_e_exato_em_decimal():
    itens = [ItemCarrinho(1, 3), ItemCarrinho(2, 1)]
    produtos = {1: produto(1, preco="59.90"), 2: produto(2, "Teclado", "120.50")}
    assert domain.total(domain.montar_linhas(itens, produtos)) == Decimal("300.20")


@pytest.mark.parametrize("item,prod,mensagem", [
    (ItemCarrinho(1, 6), produto(estoque=5), "Mouse: restam 5, você pediu 6."),
    (ItemCarrinho(1, 1), produto(ativo=False), "Mouse não está mais disponível."),
    (ItemCarrinho(1, 1), None, "Um produto não está mais disponível."),
])
def test_problemas_do_pedido(item, prod, mensagem):
    produtos = {1: prod} if prod else {}
    assert domain.problemas([item], domain.montar_linhas([item], produtos)) == [mensagem]


def test_problemas_lista_todos_de_uma_vez():
    itens = [ItemCarrinho(1, 9), ItemCarrinho(2, 1)]
    produtos = {1: produto(1, estoque=2), 2: produto(2, "Teclado", ativo=False)}
    assert len(domain.problemas(itens, domain.montar_linhas(itens, produtos))) == 2


# ------------------------------------------------------------------ serviço + repositório em memória
def repo(**kw):
    return MemoriaPedidoRepository(carrinhos={"ana": [ItemCarrinho(1, 2)]}, produtos={1: produto(estoque=5)}, **kw)


def test_cria_pedido_baixa_estoque_e_esvazia_carrinho():
    r = repo()
    pedido = create_order("ana", r)
    assert pedido.total == Decimal("119.80") and r.produtos[1].estoque == 3 and r.carrinhos["ana"] == []


def test_carrinho_vazio_ou_inexistente():
    with pytest.raises(EmptyCartError):
        create_order("bia", repo())
    r = repo(); r.carrinhos["ana"] = []
    with pytest.raises(EmptyCartError):
        create_order("ana", r)


def test_sem_estoque_nao_grava_nada():
    r = repo(); r.produtos[1] = produto(estoque=1)
    with pytest.raises(StockError, match="restam 1, você pediu 2"):
        create_order("ana", r)
    assert r.pedidos == [] and r.produtos[1].estoque == 1 and len(r.carrinhos["ana"]) == 1


def test_estoque_que_mudou_no_meio_levanta_erro():
    class Concorrente(MemoriaPedidoRepository):
        def baixar_estoque(self, product_id, quantidade):
            return False                                          # outro comprador levou a última unidade
    r = Concorrente(carrinhos={"ana": [ItemCarrinho(1, 2)]}, produtos={1: produto(estoque=5)})
    with pytest.raises(StockError, match="o estoque mudou"):
        create_order("ana", r)


def test_falha_no_meio_desfaz_tudo_como_uma_transacao_de_verdade():
    class SegundoFalha(MemoriaPedidoRepository):
        def baixar_estoque(self, product_id, quantidade):
            return False if product_id == 2 else super().baixar_estoque(product_id, quantidade)
    r = SegundoFalha(carrinhos={"ana": [ItemCarrinho(1, 2), ItemCarrinho(2, 1)]},
                     produtos={1: produto(1, estoque=5), 2: produto(2, "Teclado", "120.50", estoque=3)})
    with pytest.raises(StockError):
        create_order("ana", r)
    assert r.produtos[1].estoque == 5 and r.pedidos == [] and len(r.carrinhos["ana"]) == 2        # rollback: nada mudou
