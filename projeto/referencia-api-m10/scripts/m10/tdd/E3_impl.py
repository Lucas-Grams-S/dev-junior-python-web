from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Cupom:
    tipo: str
    valor: Decimal


def calcular_desconto(cupom, subtotal):
    if cupom.tipo == "fixo":
        return cupom.valor.quantize(Decimal("0.01"))
    return (subtotal * cupom.valor / 100).quantize(Decimal("0.01"))
