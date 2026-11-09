"""O 'fake' mentiroso: sem transação de verdade, uma falha no meio deixa o mundo pela metade. Corrigindo com snapshot/rollback."""
from contextlib import nullcontext
from decimal import Decimal

from apps.orders.domain import ItemCarrinho, ProdutoInfo
from apps.orders.repositories import MemoriaPedidoRepository
from apps.orders.services import StockError, create_order


class ConcorrenteNoSegundo(MemoriaPedidoRepository):
    """Simula outro comprador levando o 2º produto DEPOIS da validação (a baixa do 2º falha)."""

    def baixar_estoque(self, product_id, quantidade):
        if product_id == 2:
            return False
        return super().baixar_estoque(product_id, quantidade)


class SemTransacao(ConcorrenteNoSegundo):
    """O fake 'de antes': transacao() não faz nada."""

    def transacao(self):
        return nullcontext()


# (ConcorrenteNoSegundo herda de MemoriaPedidoRepository a transacao() REAL: foto do estado + restauração em caso de erro)


def cenario(classe):
    r = classe(carrinhos={"ana": [ItemCarrinho(1, 2), ItemCarrinho(2, 1)]},
               produtos={1: ProdutoInfo(1, "Mouse", Decimal("59.90"), 5, True), 2: ProdutoInfo(2, "Teclado", Decimal("120.50"), 3, True)})
    try:
        create_order("ana", r)
    except StockError as e:
        print(f"  erro esperado: {e}")
    return r


for nome, classe in (("transacao() = nullcontext (o fake ingênuo)", SemTransacao), ("transacao() com foto do estado e restauração (o fake atual)", ConcorrenteNoSegundo)):
    print(nome)
    r = cenario(classe)
    print(f"  estoque do Mouse: {r.produtos[1].estoque} (era 5) | pedidos gravados: {len(r.pedidos)} | itens no carrinho: {len(r.carrinhos['ana'])}")
    print("  →", "INCONSISTENTE: o Mouse foi baixado e o pedido ficou criado, mas a operação falhou" if r.produtos[1].estoque != 5 else "CONSISTENTE: nada mudou")
