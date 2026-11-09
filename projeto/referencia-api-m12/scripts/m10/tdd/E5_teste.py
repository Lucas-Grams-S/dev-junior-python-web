from datetime import date

import pytest

from apps.orders.cupons import CupomInvalido


def test_cupom_vencido_e_recusado():
    cupom = Cupom(tipo="percentual", valor=Decimal("10"), valido_ate=date(2026, 11, 7))
    with pytest.raises(CupomInvalido, match="venceu"):
        calcular_desconto(cupom, Decimal("200"), hoje=date(2026, 11, 8))


def test_no_ultimo_dia_de_validade_ainda_vale():
    cupom = Cupom(tipo="percentual", valor=Decimal("10"), valido_ate=date(2026, 11, 8))
    assert calcular_desconto(cupom, Decimal("200"), hoje=date(2026, 11, 8)) == Decimal("20.00")
