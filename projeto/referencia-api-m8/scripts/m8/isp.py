"""Segregação de interfaces: dependa SÓ do que usa. O mypy verifica de verdade (a porta é um Protocol)."""
from decimal import Decimal
from typing import Protocol


class PedidoRepository(Protocol):                 # a porta "gorda" (7 métodos), como em apps/orders/repositories.py
    def travar_produtos(self, ids: list[int]) -> dict[int, "Produto"]: ...
    def baixar_estoque(self, product_id: int, quantidade: int) -> bool: ...
    def criar_pedido(self, user: str, total: Decimal) -> object: ...
    def esvaziar_carrinho(self, carrinho: object) -> None: ...


class Produto:
    def __init__(self, nome: str, estoque: int) -> None:
        self.nome, self.estoque = nome, estoque


class LeitorDeProdutos(Protocol):                 # a interface MÍNIMA que um relatório de estoque realmente precisa
    def travar_produtos(self, ids: list[int]) -> dict[int, Produto]: ...


def relatorio_de_estoque(leitor: LeitorDeProdutos, ids: list[int]) -> list[str]:
    return [f"{p.nome}: {p.estoque}" for p in leitor.travar_produtos(ids).values()]


class FakeSoDeLeitura:                            # tem APENAS o método que o relatório usa
    def travar_produtos(self, ids: list[int]) -> dict[int, Produto]:
        return {1: Produto("Mouse", 5)}


class SemOMetodo:
    def listar(self) -> list[int]:
        return []


print(relatorio_de_estoque(FakeSoDeLeitura(), [1]))       # ok: o fake é minúsculo (3 linhas), não precisa implementar 7 métodos
print(relatorio_de_estoque(SemOMetodo(), [1]))            # o mypy deve apontar o erro AQUI, antes de rodar
