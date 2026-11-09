import json
from decimal import Decimal
from pathlib import Path

import pytest
from src.relatorio import LinhaInvalida, main, parse_preco, processar

DADOS = Path(__file__).parent.parent / "dados" / "vendas.csv"


@pytest.mark.parametrize(
    ("txt", "v"), [("29.90", "29.90"), ("1.250,00", "1250.00"), ("15.5", "15.5"), ("0", "0"), ("7,5", "7.5")]
)
def test_parse_preco_ok(txt, v):
    assert parse_preco(txt) == Decimal(v)


@pytest.mark.parametrize("txt", ["-5.00", "abc", "1,250,00", "1,250.00", "NaN", "Infinity", ""])
def test_parse_preco_rejeita(txt):
    with pytest.raises(LinhaInvalida):
        parse_preco(txt)


def test_relatorio_do_arquivo_de_exemplo():
    r = processar(DADOS)
    assert r.lidas == 16 and len(r.rejeitadas) == 6
    assert r.receita_total == Decimal("4603.90")
    assert dict(r.receita_por_dia) == {
        "2026-11-01": Decimal("258.80"),
        "2026-11-02": Decimal("1648.00"),
        "2026-11-04": Decimal("2697.10"),
    }
    assert [n for n, _ in r.rejeitadas] == [7, 8, 9, 10, 11, 12]


def test_somente_pagos_e_empate_alfabetico(tmp_path):
    p = tmp_path / "v.csv"
    p.write_text(
        "pedido_id,data,sku,quantidade,preco_unitario,status\n"
        "1,2026-01-01,B,2,1.00,pago\n2,2026-01-01,A,2,1.00,pago\n3,2026-01-01,C,9,1.00,cancelado\n"
    )
    r = processar(p)
    assert r.receita_total == Decimal("4.00")
    assert list(r.quantidade_por_sku.most_common()) == [("B", 2), ("A", 2)]  # C não entra


def test_cabecalho_errado_e_coluna_extra(tmp_path):
    p = tmp_path / "v.csv"
    p.write_text("a,b\n1,2\n")
    with pytest.raises(ValueError, match="cabeçalho"):
        processar(p)
    q = tmp_path / "w.csv"
    q.write_text(
        "pedido_id,data,sku,quantidade,preco_unitario,status\n1,2026-01-01,A,1,1.00,pago,SOBRA\n2,2026-01-01,A,1\n"
    )
    r = processar(q)
    assert [m for _, m in r.rejeitadas] == ["número de colunas incorreto"] * 2


def test_cli_json_e_codigo_de_saida(capsys, tmp_path):
    assert main([str(DADOS), "--json"]) == 0
    j = json.loads(capsys.readouterr().out)
    assert j["receita_total"] == "4603.90" and j["top_skus"][0] == {"sku": "INF-001", "quantidade": 6}
    assert main([str(tmp_path / "nada.csv")]) == 2


def test_arquivo_grande_em_fluxo(tmp_path):
    """200 mil linhas (7,2 MB): leitura por linha. Medido: pico ~19,9 MB, dominado pelo conjunto de ids vistos (O(ids únicos))."""
    import tracemalloc

    p = tmp_path / "grande.csv"
    with p.open("w") as f:
        f.write("pedido_id,data,sku,quantidade,preco_unitario,status\n")
        for i in range(200_000):
            f.write(f"{i},2026-01-01,SKU-{i % 50},1,2.50,pago\n")
    tracemalloc.start()
    r = processar(p)
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert r.receita_total == Decimal("500000.00")
    assert pico < 40 * 1024 * 1024, (
        pico
    )  # folga p/ variação; o limite real é o conjunto de ids (ver README: o que ficou de fora)
