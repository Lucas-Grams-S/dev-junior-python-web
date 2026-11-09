"""Guarda de regressão: construções que DESLIGAM proteções do framework não entram no código sem alguém decidir de propósito."""

import pathlib
import re

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PADROES = {
    "SQL cru por .raw()/.extra()": r"\.(raw|extra)\(",
    "mark_safe": r"\bmark_safe\(",
    "filtro |safe": r"\|\s*safe\b",
    "autoescape off": r"autoescape\s+off",
    "csrf_exempt": r"\bcsrf_exempt\b",
}
# Exceções JUSTIFICADAS (arquivo -> padrão): o webhook é autenticado por assinatura HMAC, não por cookie (aula 7.09).
PERMITIDO = {("apps/payments/api.py", "csrf_exempt")}


def arquivos():
    for pasta in ("apps", "config"):
        for p in (RAIZ / pasta).rglob("*"):
            if p.suffix in {".py", ".html", ".txt"} and "migrations" not in p.parts and "tests" not in p.parts:
                yield p


@pytest.mark.parametrize("nome,padrao", PADROES.items())
def test_sem_construcao_perigosa(nome, padrao):
    achados = []
    for p in arquivos():
        rel = str(p.relative_to(RAIZ))
        for n, linha in enumerate(p.read_text(errors="ignore").splitlines(), 1):
            if re.search(padrao, linha) and (rel, nome) not in PERMITIDO and not linha.lstrip().startswith("#"):
                achados.append(f"{rel}:{n}: {linha.strip()[:80]}")
    assert not achados, f"{nome} sem justificativa registrada:\n" + "\n".join(achados)


def test_a_excecao_do_webhook_ainda_existe_ou_a_lista_esta_velha():
    texto = (RAIZ / "apps/payments/api.py").read_text()
    assert "csrf_exempt" in texto, "remova a exceção de PERMITIDO: ela não é mais necessária"


@pytest.mark.django_db
def test_respostas_json_trazem_nosniff(client):
    r = client.get("/api/v1/categories/")
    assert r["Content-Type"].startswith("application/json") and r["X-Content-Type-Options"] == "nosniff"
