from dataclasses import dataclass
from datetime import date
from decimal import Decimal


class CupomInvalido(Exception):
    pass


@dataclass(frozen=True)
class Cupom:
    tipo: str
    valor: Decimal
    valido_ate: date | None = None


def calcular_desconto(cupom, subtotal, hoje=None):
    if cupom.valido_ate is not None and hoje > cupom.valido_ate:
        raise CupomInvalido(f"O cupom venceu em {cupom.valido_ate:%d/%m/%Y}.")
    if cupom.tipo == "fixo":
        desconto = cupom.valor
    else:
        desconto = subtotal * cupom.valor / 100
    return min(desconto, subtotal).quantize(Decimal("0.01"))
