

def test_desconto_nunca_passa_do_subtotal():
    assert calcular_desconto(Cupom(tipo="fixo", valor=Decimal("500")), Decimal("120")) == Decimal("120.00")
