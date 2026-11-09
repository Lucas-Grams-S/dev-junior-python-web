

def test_cupom_de_valor_fixo():
    assert calcular_desconto(Cupom(tipo="fixo", valor=Decimal("25")), Decimal("200")) == Decimal("25.00")
