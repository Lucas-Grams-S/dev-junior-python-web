from decimal import Decimal

FRETE_PADRAO = Decimal("19.90")
LIMITE_FRETE_GRATIS = Decimal("200.00")


def calcular_frete(subtotal: Decimal) -> Decimal:
    """Frete grátis a partir de R$ 200,00; senão, R$ 19,90."""
    return Decimal("0") if subtotal >= LIMITE_FRETE_GRATIS else FRETE_PADRAO
