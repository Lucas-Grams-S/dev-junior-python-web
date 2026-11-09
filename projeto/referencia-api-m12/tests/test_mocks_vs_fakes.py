"""Três jeitos de testar o MESMO caso de uso (create_order): com um FAKE (estado) e com MOCKS (interações)."""

from decimal import Decimal
from unittest.mock import create_autospec

from apps.orders import services
from apps.orders.domain import ItemCarrinho, ProdutoInfo
from apps.orders.repositories import MemoriaPedidoRepository, PedidoRepository


def repo_com_fake():
    p = ProdutoInfo(1, "Caneta", Decimal("10.00"), 5, True)
    return MemoriaPedidoRepository(carrinhos={"ana": [ItemCarrinho(1, 2)]}, produtos={1: p})


def test_estado_com_fake_o_resultado_importa():
    repo = repo_com_fake()
    pedido = services.create_order("ana", repo=repo)
    assert pedido.total == 20 and repo.produtos[1].estoque == 3 and repo.carrinhos["ana"] == []


def mock_do_repo():
    repo = create_autospec(PedidoRepository, instance=True)
    repo.itens_do_carrinho.return_value = [ItemCarrinho(1, 2)]
    repo.travar_produtos.return_value = {1: ProdutoInfo(1, "Caneta", Decimal("10.00"), 5, True)}
    repo.baixar_estoque.return_value = True
    return repo


def test_mock_sequencia_exata_de_chamadas():
    repo = mock_do_repo()
    services.create_order("ana", repo=repo)
    nomes = [c[0] for c in repo.mock_calls if not c[0].startswith("transacao")]
    assert nomes == ["travar_carrinho", "itens_do_carrinho", "travar_produtos", "criar_pedido", "baixar_estoque", "esvaziar_carrinho"]


def test_mock_so_o_essencial():
    repo = mock_do_repo()
    services.create_order("ana", repo=repo)
    repo.criar_pedido.assert_called_once()
    repo.esvaziar_carrinho.assert_called_once()
