"""Relatório de vendas (take-home 1). Lê o CSV em fluxo (uma linha por vez), valida e agrega."""

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

COLUNAS = ["pedido_id", "data", "sku", "quantidade", "preco_unitario", "status"]
STATUS = {"pago", "cancelado", "pendente", "reembolsado"}


@dataclass
class Resultado:
    receita_total: Decimal = Decimal(0)
    receita_por_dia: dict[str, Decimal] = field(default_factory=lambda: defaultdict(Decimal))
    quantidade_por_sku: Counter = field(default_factory=Counter)
    rejeitadas: list[tuple[int, str]] = field(default_factory=list)
    lidas: int = 0


class LinhaInvalida(ValueError):
    pass


def parse_preco(texto: str) -> Decimal:
    """Aceita '29.90' e o formato brasileiro '1.250,00'. Ambíguo (ex.: '1,250')? Rejeita em vez de adivinhar."""
    t = texto.strip()
    if "," in t:
        if t.count(",") != 1 or t.rfind(",") < t.rfind("."):
            raise LinhaInvalida(f"preço ambíguo: {texto!r}")
        t = t.replace(".", "").replace(",", ".")
    try:
        v = Decimal(t)
    except InvalidOperation:
        raise LinhaInvalida(f"preço inválido: {texto!r}") from None
    if not v.is_finite() or v < 0:
        raise LinhaInvalida(f"preço negativo ou inválido: {texto!r}")
    return v


def validar(linha: dict[str, str], vistos: set[str]) -> tuple[str, date, str, int, Decimal, str]:
    pid = (linha["pedido_id"] or "").strip()
    if not pid:
        raise LinhaInvalida("pedido_id vazio")
    if pid in vistos:
        raise LinhaInvalida(f"pedido_id duplicado: {pid}")
    try:
        data = date.fromisoformat(linha["data"].strip())
    except ValueError:
        raise LinhaInvalida(f"data inválida: {linha['data']!r}") from None
    sku = linha["sku"].strip().upper()
    if not sku:
        raise LinhaInvalida("SKU vazio")
    try:
        qtd = int(linha["quantidade"])
    except ValueError:
        raise LinhaInvalida(f"quantidade não numérica: {linha['quantidade']!r}") from None
    if qtd <= 0:
        raise LinhaInvalida(f"quantidade deve ser > 0: {qtd}")
    status = linha["status"].strip().lower()
    if status not in STATUS:
        raise LinhaInvalida(f"status desconhecido: {status!r}")
    return pid, data, sku, qtd, parse_preco(linha["preco_unitario"]), status


def processar(caminho: Path) -> Resultado:
    r = Resultado()
    vistos: set[str] = set()
    with caminho.open(newline="", encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        if leitor.fieldnames != COLUNAS:
            raise ValueError(f"cabeçalho esperado {COLUNAS}, recebido {leitor.fieldnames}")
        for n, linha in enumerate(leitor, start=2):  # linha 1 é o cabeçalho
            r.lidas += 1
            try:
                if None in linha or None in linha.values():
                    raise LinhaInvalida("número de colunas incorreto")
                pid, data, sku, qtd, preco, status = validar(linha, vistos)
            except LinhaInvalida as e:
                r.rejeitadas.append((n, str(e)))
                continue
            vistos.add(pid)
            if status == "pago":  # só pedidos pagos contam para receita e para o ranking
                valor = preco * qtd
                r.receita_total += valor
                r.receita_por_dia[data.isoformat()] += valor
                r.quantidade_por_sku[sku] += qtd
    return r


def top_skus(r: Resultado, k: int = 3) -> list[tuple[str, int]]:
    return sorted(r.quantidade_por_sku.items(), key=lambda p: (-p[1], p[0]))[:k]


def como_dict(r: Resultado) -> dict:
    return {
        "linhas_lidas": r.lidas,
        "receita_total": str(r.receita_total),
        "receita_por_dia": {d: str(v) for d, v in sorted(r.receita_por_dia.items())},
        "top_skus": [{"sku": s, "quantidade": q} for s, q in top_skus(r)],
        "rejeitadas": [{"linha": n, "motivo": m} for n, m in r.rejeitadas],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="relatorio")
    ap.add_argument("arquivo", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        r = processar(args.arquivo)
    except (OSError, ValueError) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(como_dict(r), ensure_ascii=False, indent=2))
        return 0
    print(f"Linhas lidas: {r.lidas}  |  rejeitadas: {len(r.rejeitadas)}")
    print(f"Receita total (pedidos pagos): R$ {r.receita_total:.2f}")
    print("Receita por dia:")
    for d, v in sorted(r.receita_por_dia.items()):
        print(f"  {d}  R$ {v:.2f}")
    print("Top SKUs:", ", ".join(f"{s} ({q})" for s, q in top_skus(r)))
    print("Rejeitadas:")
    for n, m in r.rejeitadas:
        print(f"  linha {n}: {m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
