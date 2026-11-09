import pytest

from legado.precificacao import CUPONS, PedidoInvalido, ajuste_pagamento, desconto_cupom, frete, precificar


@pytest.mark.parametrize(
    "total,cupom,esperado",
    [(100, None, 0), (100, "", 0), (100, "PROMO10", 10), (600, "PROMO20", 120), (500, "PROMO20", 50), (300, "FRETEGRATIS", 0)],
)
def test_desconto_por_cupom(total, cupom, esperado):
    assert desconto_cupom(total, cupom) == pytest.approx(esperado)


def test_cupom_desconhecido_e_forma_desconhecida_sao_rejeitados():
    with pytest.raises(PedidoInvalido, match="cupom"):
        desconto_cupom(100, "XPTO")
    with pytest.raises(PedidoInvalido, match="forma"):
        ajuste_pagamento(100, None)


def test_fronteira_do_frete_e_200_exato():
    assert frete(200, 0, None) == 0 and frete(199.99, 0, None) == 19.9
    assert frete(50, 0, "FRETEGRATIS") == 0


def test_cupom_novo_e_uma_linha_na_tabela(monkeypatch):
    monkeypatch.setitem(CUPONS, "BLACK30", lambda total: total * 0.30)
    assert precificar(100, "BLACK30", "cartao") == (pytest.approx(30), 19.9, 89.9)
