from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal


class CupomInvalido(Exception):
    pass


@dataclass(frozen=True)
class Cupom:
    tipo: str
    valor: Decimal
    valido_ate: date | None = None
    minimo: Decimal = Decimal("0")


def calcular_desconto(cupom, subtotal, hoje=None):
    if cupom.valido_ate is not None and hoje > cupom.valido_ate:
        raise CupomInvalido(f"O cupom venceu em {cupom.valido_ate:%d/%m/%Y}.")
    if subtotal < cupom.minimo:
        raise CupomInvalido(f"Pedido mínimo de R$ {cupom.minimo} para este cupom.")
    if cupom.tipo == "fixo":
        desconto = cupom.valor
    else:
        desconto = subtotal * cupom.valor / 100
    return min(desconto, subtotal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
