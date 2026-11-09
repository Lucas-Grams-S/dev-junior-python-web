

def test_subtotal_abaixo_do_minimo_e_recusado():
    cupom = Cupom(tipo="percentual", valor=Decimal("10"), minimo=Decimal("100"))
    with pytest.raises(CupomInvalido, match="mínimo"):
        calcular_desconto(cupom, Decimal("99.99"))


def test_subtotal_exatamente_no_minimo_vale():
    cupom = Cupom(tipo="percentual", valor=Decimal("10"), minimo=Decimal("100"))
    assert calcular_desconto(cupom, Decimal("100")) == Decimal("10.00")


def test_arredonda_meio_centavo_para_cima():
    # 33,35% de 10,01 = 3,338335 -> 3,34 ; e 12,5% de 0,10 = 0,0125 -> 0,01
    assert calcular_desconto(Cupom(tipo="percentual", valor=Decimal("33.35")), Decimal("10.01")) == Decimal("3.34")
    assert calcular_desconto(Cupom(tipo="percentual", valor=Decimal("50")), Decimal("0.05")) == Decimal("0.03")   # 0,025 -> 0,03
