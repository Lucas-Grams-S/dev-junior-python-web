"""Regras de negócio do pedido, em Python PURO: sem Django, sem banco, sem HTTP. Por isso testam em milissegundos."""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ProdutoInfo:
    id: int
    nome: str
    preco: Decimal
    estoque: int
    ativo: bool


@dataclass(frozen=True)
class ItemCarrinho:
    product_id: int
    quantidade: int


@dataclass(frozen=True)
class LinhaCompra:
    """Um item do carrinho já cruzado com o produto: o que o pedido vai congelar."""

    product_id: int
    nome: str
    quantidade: int
    preco: Decimal
    estoque: int
    ativo: bool

    @property
    def subtotal(self) -> Decimal:
        return self.quantidade * self.preco


def montar_linhas(itens: Sequence[ItemCarrinho], produtos: Mapping[int, ProdutoInfo]) -> list[LinhaCompra]:
    """Cruza os itens do carrinho com os produtos (o que não existir fica de fora; `problemas` acusa)."""
    linhas: list[LinhaCompra] = []
    for i in itens:
        p = produtos.get(i.product_id)
        if p is not None:
            linhas.append(LinhaCompra(p.id, p.nome, i.quantidade, p.preco, p.estoque, p.ativo))
    return linhas


def problemas(itens: Sequence[ItemCarrinho], linhas: Sequence[LinhaCompra]) -> list[str]:
    """Lista TODOS os motivos pelos quais o pedido não pode ser feito (mensagem completa para o usuário)."""
    achados: list[str] = []
    por_id = {linha.product_id: linha for linha in linhas}
    for item in itens:
        linha = por_id.get(item.product_id)
        if linha is None:
            achados.append("Um produto não está mais disponível.")
        elif not linha.ativo:
            achados.append(f"{linha.nome} não está mais disponível.")
        elif item.quantidade > linha.estoque:
            achados.append(f"{linha.nome}: restam {linha.estoque}, você pediu {item.quantidade}.")
    return achados


def total(linhas: Iterable[LinhaCompra]) -> Decimal:
    return sum((linha.subtotal for linha in linhas), Decimal("0"))
