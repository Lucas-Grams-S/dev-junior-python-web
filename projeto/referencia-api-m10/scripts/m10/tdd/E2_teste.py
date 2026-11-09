

def test_triangulacao_outro_percentual_e_outro_subtotal():
    assert calcular_desconto(Cupom(tipo="percentual", valor=Decimal("15")), Decimal("80")) == Decimal("12.00")
