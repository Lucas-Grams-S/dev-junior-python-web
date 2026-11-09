"""Testes escritos a partir do REQUISITO (e não da sugestão): é assim que se desconfia com método."""
import sqlite3
import pytest
from sugestao_ia import aplicar_cupom


@pytest.fixture
def banco(tmp_path):
    caminho = str(tmp_path / "cupons.sqlite3")
    con = sqlite3.connect(caminho)
    con.execute("CREATE TABLE cupons (codigo TEXT, percentual REAL)")
    con.execute("INSERT INTO cupons VALUES ('PROMO10', 10), ('METADE', 50)")
    con.commit(); con.close()
    return caminho


def test_cupom_valido_desconta(banco):
    assert aplicar_cupom(200.0, "PROMO10", banco) == 180.0              # o caminho feliz funciona


def test_cupom_inexistente_deve_ser_recusado(banco):
    with pytest.raises(Exception):
        aplicar_cupom(200.0, "NAOEXISTE", banco)                         # requisito: recusar, não ignorar em silêncio


def test_erro_de_infraestrutura_nao_pode_virar_desconto_zero(tmp_path):
    with pytest.raises(Exception):
        aplicar_cupom(200.0, "PROMO10", str(tmp_path / "banco_que_nao_tem_a_tabela.sqlite3"))   # tabela ausente: deve estourar


def test_meio_centavo_para_cima(banco):
    assert aplicar_cupom(10.05, "METADE", banco) == 5.03                 # 10,05 com 50% = 5,025 → 5,03


def test_aspas_no_codigo_do_cupom_nao_quebra_a_consulta(banco):
    with pytest.raises(Exception, match="recus|inv|exist"):
        aplicar_cupom(200.0, "O'BRIEN", banco)                           # texto comum com apóstrofo: deve ser 'cupom inexistente'
