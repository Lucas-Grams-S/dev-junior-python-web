"""Regras de cupom desenvolvidas com TDD (aula 10.04): cada teste nasceu ANTES do código que o satisfaz."""

import random
from datetime import date
from decimal import Decimal

import pytest

from apps.orders.cupons import Cupom, CupomInvalido, calcular_desconto

D = Decimal


# ciclo 1 e 2 (triangulação: dois casos obrigam a escrever a fórmula de verdade, não um valor fixo)
@pytest.mark.parametrize(
    "percentual,subtotal,esperado", [("10", "200", "20.00"), ("15", "80", "12.00")], ids=["10pct-de-200", "15pct-de-80"]
)
def test_cupom_percentual(percentual, subtotal, esperado):
    assert calcular_desconto(Cupom(tipo="percentual", valor=D(percentual)), D(subtotal)) == D(esperado)


# ciclo 3
def test_cupom_de_valor_fixo():
    assert calcular_desconto(Cupom(tipo="fixo", valor=D("25")), D("200")) == D("25.00")


# ciclo 4
def test_desconto_nunca_passa_do_subtotal():
    assert calcular_desconto(Cupom(tipo="fixo", valor=D("500")), D("120")) == D("120.00")


# ciclo 5: o relógio é INJETADO (`hoje`), nada de datetime.now() escondido
def test_cupom_vencido_e_recusado():
    cupom = Cupom(tipo="percentual", valor=D("10"), valido_ate=date(2026, 11, 7))
    with pytest.raises(CupomInvalido, match="venceu"):
        calcular_desconto(cupom, D("200"), hoje=date(2026, 11, 8))


def test_no_ultimo_dia_de_validade_ainda_vale():
    cupom = Cupom(tipo="percentual", valor=D("10"), valido_ate=date(2026, 11, 8))
    assert calcular_desconto(cupom, D("200"), hoje=date(2026, 11, 8)) == D("20.00")


# ciclo 6: fronteira do mínimo (99,99 recusa, 100,00 vale) e arredondamento
def test_subtotal_abaixo_do_minimo_e_recusado():
    cupom = Cupom(tipo="percentual", valor=D("10"), minimo=D("100"))
    with pytest.raises(CupomInvalido, match="mínimo"):
        calcular_desconto(cupom, D("99.99"))


def test_subtotal_exatamente_no_minimo_vale():
    assert calcular_desconto(Cupom(tipo="percentual", valor=D("10"), minimo=D("100")), D("100")) == D("10.00")


def test_arredonda_meio_centavo_para_cima():
    assert calcular_desconto(Cupom(tipo="percentual", valor=D("33.35")), D("10.01")) == D("3.34")
    assert calcular_desconto(Cupom(tipo="percentual", valor=D("50")), D("0.05")) == D("0.03")  # 0,025 -> 0,03 (não 0,02)


# ciclo 7
def test_tipo_de_cupom_desconhecido_e_erro_claro():
    with pytest.raises(CupomInvalido, match="tipo"):
        calcular_desconto(Cupom(tipo="misterioso", valor=D("10")), D("100"))


# propriedade: para QUALQUER entrada válida, 0 <= desconto <= subtotal e o resultado tem 2 casas
def test_propriedade_desconto_entre_zero_e_subtotal():
    sorteio = random.Random(2026)  # semente fixa: o teste é determinístico
    for _ in range(500):
        subtotal = D(sorteio.randint(1, 1_000_000)) / 100
        tipo = sorteio.choice(["percentual", "fixo"])
        valor = D(sorteio.randint(0, 20_000)) / 100
        desconto = calcular_desconto(Cupom(tipo=tipo, valor=valor), subtotal)
        assert D("0") <= desconto <= subtotal
        assert desconto == desconto.quantize(D("0.01"))


# bug achado pelo mypy: cupom COM validade chamado SEM `hoje` quebrava com TypeError (None > date)
def test_sem_informar_hoje_usa_a_data_de_hoje():
    vencido = Cupom(tipo="percentual", valor=D("10"), valido_ate=date(2000, 1, 1))
    futuro = Cupom(tipo="percentual", valor=D("10"), valido_ate=date(2999, 1, 1))
    with pytest.raises(CupomInvalido, match="venceu"):
        calcular_desconto(vencido, D("200"))
    assert calcular_desconto(futuro, D("200")) == D("20.00")
