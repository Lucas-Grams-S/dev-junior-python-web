from decimal import Decimal

from apps.orders.cupons import Cupom, calcular_desconto


def test_cupom_percentual_de_10_sobre_200_da_20():
    assert calcular_desconto(Cupom(tipo="percentual", valor=Decimal("10")), Decimal("200")) == Decimal("20.00")
