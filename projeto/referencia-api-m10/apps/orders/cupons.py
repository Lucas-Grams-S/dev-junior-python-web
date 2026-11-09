"""Regras de desconto de cupons: código PURO (sem banco, sem relógio global), desenvolvido com TDD (aula 10.04)."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

CENTAVO = Decimal("0.01")


class CupomInvalido(Exception):
    pass


@dataclass(frozen=True)
class Cupom:
    tipo: str  # "percentual" | "fixo"
    valor: Decimal
    valido_ate: date | None = None
    minimo: Decimal = Decimal("0")


# Cada tipo é uma função (cupom, subtotal) -> desconto bruto. Tipo novo = uma linha aqui (e um teste).
TIPOS: dict[str, Callable[[Cupom, Decimal], Decimal]] = {
    "percentual": lambda cupom, subtotal: subtotal * cupom.valor / 100,
    "fixo": lambda cupom, subtotal: cupom.valor,
}


def calcular_desconto(cupom: Cupom, subtotal: Decimal, hoje: date | None = None) -> Decimal:
    """Desconto em reais (2 casas, meio centavo para cima), nunca maior que o subtotal. `hoje` é injetado para testar a validade."""
    hoje = hoje or date.today()  # sem data informada, vale o dia de hoje (nos testes, injete `hoje`)
    if cupom.tipo not in TIPOS:
        raise CupomInvalido(f"tipo de cupom desconhecido: {cupom.tipo!r}")
    if cupom.valido_ate is not None and hoje > cupom.valido_ate:
        raise CupomInvalido(f"O cupom venceu em {cupom.valido_ate:%d/%m/%Y}.")
    if subtotal < cupom.minimo:
        raise CupomInvalido(f"Pedido mínimo de R$ {cupom.minimo} para este cupom.")
    bruto = TIPOS[cupom.tipo](cupom, subtotal)
    desconto: Decimal = min(bruto, subtotal).quantize(CENTAVO, rounding=ROUND_HALF_UP)
    return desconto
