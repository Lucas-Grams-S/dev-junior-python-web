from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Cupom:
    tipo: str
    valor: Decimal


def calcular_desconto(cupom, subtotal):
    if cupom.tipo == "fixo":
        desconto = cupom.valor
    else:
        desconto = subtotal * cupom.valor / 100
    return min(desconto, subtotal).quantize(Decimal("0.01"))
