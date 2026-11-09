"""Regras de preço do legado, PURAS (sem banco, sem I/O).

Extraídas de `processar_pedido`; o comportamento (inclusive em float) é o mesmo."""

from collections.abc import Callable


class PedidoInvalido(Exception):
    pass


# Cada cupom é uma função (total -> desconto). Cupom novo = uma linha na tabela, sem mexer em nenhum `if`.
CUPONS: dict[str, Callable[[float], float]] = {
    "PROMO10": lambda total: total * 0.10,
    "PROMO20": lambda total: total * 0.20 if total > 500 else total * 0.10,
    "FRETEGRATIS": lambda total: 0,
}
# Ajuste por forma de pagamento (positivo = desconto; negativo = acréscimo).
FORMAS_PAGAMENTO: dict[str, Callable[[float], float]] = {
    "pix": lambda total: total * 0.05,
    "cartao": lambda total: 0,
    "boleto": lambda total: -2.5,
}
FRETE_PADRAO: float = 19.9
FRETE_GRATIS_ACIMA_DE: float = 200


def desconto_cupom(total: float, cupom: str | None) -> float:
    if not cupom:
        return 0
    if cupom not in CUPONS:
        raise PedidoInvalido("cupom invalido")
    return CUPONS[cupom](total)


def ajuste_pagamento(total: float, forma: str | None) -> float:
    if forma is None or forma not in FORMAS_PAGAMENTO:
        raise PedidoInvalido("forma de pagamento invalida")
    return FORMAS_PAGAMENTO[forma](total)


def frete(total: float, desconto: float, cupom: str | None) -> float:
    if cupom == "FRETEGRATIS":
        return 0
    return FRETE_PADRAO if total - desconto < FRETE_GRATIS_ACIMA_DE else 0


def precificar(total: float, cupom: str | None, forma: str | None) -> tuple[float, float, float]:
    """(desconto, frete, valor final arredondado)"""
    desc = desconto_cupom(total, cupom) + ajuste_pagamento(total, forma)
    f = frete(total, desc, cupom)
    return desc, f, round(total - desc + f, 2)
