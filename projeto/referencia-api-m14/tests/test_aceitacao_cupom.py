"""Critérios de aceitação da história 'aplicar cupom' (docs/historias/cupom.md), um teste por critério, no formato Dado/Quando/Então."""

from datetime import date
from decimal import Decimal

import pytest

from apps.orders.cupons import Cupom, CupomInvalido, calcular_desconto

D = Decimal


def test_criterio_1_cupom_percentual():
    cupom = Cupom(tipo="percentual", valor=D("10"))  # Dado o cupom PROMO10 (10%)
    desconto = calcular_desconto(cupom, D("200.00"))  # Quando o subtotal é R$ 200,00
    assert desconto == D("20.00")  # Então o desconto é R$ 20,00


def test_criterio_2_desconto_limitado_ao_subtotal():
    cupom = Cupom(tipo="fixo", valor=D("500"))  # Dado um cupom fixo de R$ 500,00
    assert calcular_desconto(cupom, D("120.00")) == D("120.00")  # Quando subtotal R$ 120,00 / Então desconto R$ 120,00


def test_criterio_3_cupom_vencido_e_recusado():
    cupom = Cupom(tipo="percentual", valor=D("10"), valido_ate=date(2026, 11, 7))  # Dado um cupom válido até 07/11/2026
    with pytest.raises(CupomInvalido) as erro:
        calcular_desconto(cupom, D("200.00"), hoje=date(2026, 11, 8))  # Quando hoje é 08/11/2026
    assert str(erro.value) == "O cupom venceu em 07/11/2026."  # Então o pedido é recusado com a mensagem


def test_criterio_4_pedido_minimo():
    cupom = Cupom(tipo="percentual", valor=D("10"), minimo=D("100.00"))  # Dado um cupom com mínimo de R$ 100,00
    with pytest.raises(CupomInvalido, match="100"):
        calcular_desconto(cupom, D("99.99"))  # Quando o subtotal é R$ 99,99 / Então recusa informando o mínimo


def test_criterio_5_meio_centavo_para_cima():
    cupom = Cupom(tipo="percentual", valor=D("50"))
    assert calcular_desconto(cupom, D("0.05")) == D("0.03")  # 0,025 → R$ 0,03
