"""Logs estruturados, request_id, health checks e métricas (módulo 14, aulas 01 e 02)."""

import io
import json
import logging

import pytest
from django.test.utils import CaptureQueriesContext  # noqa: F401  (usado em outros testes do módulo)

from config.logging_json import JsonFormatter, RequestContextFilter, redigir

pytestmark = pytest.mark.django_db


@pytest.fixture
def saida_json():
    """Liga um handler JSON (o mesmo formatter da produção) ao logger de acesso e devolve o buffer."""
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RequestContextFilter())
    logger = logging.getLogger("minishop.access")
    logger.addHandler(handler)
    nivel_anterior = logger.level
    logger.setLevel(logging.DEBUG)
    yield buf
    logger.removeHandler(handler)
    logger.setLevel(nivel_anterior)


def linhas(buf):
    return [json.loads(x) for x in buf.getvalue().splitlines() if x.strip()]


def test_formatter_gera_json_valido_com_campos_fixos_e_excecao():
    handler_buf = io.StringIO()
    h = logging.StreamHandler(handler_buf)
    h.setFormatter(JsonFormatter())
    log = logging.getLogger("teste.json")
    log.addHandler(h)
    log.propagate = False
    try:
        raise ValueError("falhou ç")
    except ValueError:
        log.exception("erro ao processar", extra={"order_id": 7})
    d = json.loads(handler_buf.getvalue())
    assert {"ts", "level", "logger", "message", "request_id", "order_id", "exc"} <= set(d)
    assert d["level"] == "ERROR" and d["order_id"] == 7 and "ValueError" in d["exc"]


def test_campos_sensiveis_sao_redigidos():
    assert redigir({"user": "ana", "password": "x", "Authorization": "Bearer abc", "nested": {"api_key": "k", "ok": 1}}) == {
        "user": "ana",
        "password": "[REDACTED]",
        "Authorization": "[REDACTED]",
        "nested": {"api_key": "[REDACTED]", "ok": 1},
    }
    buf = io.StringIO()
    h = logging.StreamHandler(buf)
    h.setFormatter(JsonFormatter())
    log = logging.getLogger("teste.redacao")
    log.addHandler(h)
    log.propagate = False
    log.info("login", extra={"token": "SEGREDO", "senha": "123"})
    assert "SEGREDO" not in buf.getvalue() and "123" not in buf.getvalue()


def test_access_log_tem_request_id_status_duracao_e_nunca_a_query_string(client, saida_json):
    r = client.get("/api/v1/products/?search=cadeira&token=SEGREDO", headers={"X-Request-ID": "req-abc-12345"})
    assert r["X-Request-ID"] == "req-abc-12345"
    (linha,) = [x for x in linhas(saida_json) if x["path"].startswith("/api/v1/products")]
    assert linha["request_id"] == "req-abc-12345" and linha["status"] == r.status_code and linha["duration_ms"] >= 0
    assert "SEGREDO" not in json.dumps(linha) and "?" not in linha["path"]


def test_request_id_malicioso_e_substituido(client, saida_json):
    r = client.get("/health/", headers={"X-Request-ID": 'x\nFAKE {"level":"CRITICAL"}'})
    assert "\n" not in r["X-Request-ID"] and len(r["X-Request-ID"]) == 32  # gerou um UUID novo
    assert all("FAKE" not in json.dumps(x) for x in linhas(saida_json))


def test_request_id_e_gerado_quando_ausente(client):
    assert len(client.get("/health/")["X-Request-ID"]) == 32


def test_sondas_logam_em_debug_nao_em_info(client, saida_json):
    saida_json.truncate(0)
    logging.getLogger("minishop.access").setLevel(logging.INFO)
    client.get("/health/")
    assert linhas(saida_json) == []


def test_liveness_nao_toca_o_banco(client, django_assert_num_queries):
    with django_assert_num_queries(0):
        r = client.get("/health/")
    assert r.status_code == 200 and r.json() == {"status": "ok"}
    assert "no-cache" in r["Cache-Control"] or "max-age=0" in r["Cache-Control"]


def test_readiness_ok_com_banco_e_cache(client):
    r = client.get("/health/ready/")
    d = r.json()
    assert r.status_code == 200 and d["status"] == "ok"
    assert d["checks"]["database"]["status"] == "ok" and d["checks"]["cache"]["status"] == "ok"


def test_readiness_devolve_503_sem_vazar_detalhes_quando_o_banco_cai(client, monkeypatch, caplog):
    def quebrado(*a, **k):
        raise RuntimeError("connection to server at 10.0.3.7 refused (senha=xyz)")

    monkeypatch.setattr("config.health._banco", quebrado)
    with caplog.at_level(logging.ERROR):
        r = client.get("/health/ready/")
    assert r.status_code == 503
    corpo = r.content.decode()
    assert "10.0.3.7" not in corpo and "senha" not in corpo and r.json()["checks"]["database"] == {"status": "error"}
    assert "10.0.3.7" in caplog.text  # o detalhe vai para o LOG, não para quem pergunta


def test_readiness_so_aceita_get(client):
    assert client.post("/health/ready/").status_code == 405


def test_metrics_nao_existe_sem_token_configurado(client, settings):
    settings.METRICS_TOKEN = ""
    assert client.get("/metrics/").status_code == 404


def test_metrics_exige_o_token_e_usa_rota_nao_caminho(client, settings):
    settings.METRICS_TOKEN = "tok-metricas"
    assert client.get("/metrics/").status_code == 403
    assert client.get("/metrics/", headers={"Authorization": "Bearer errado"}).status_code == 403
    client.get("/api/v1/products/")
    client.get("/api/v1/products/999999/")
    r = client.get("/metrics/", headers={"Authorization": "Bearer tok-metricas"})
    corpo = r.content.decode()
    assert r.status_code == 200 and "minishop_http_requests_total" in corpo
    rotas = {linha.split('route="')[1].split('"')[0] for linha in corpo.splitlines() if 'route="' in linha}
    assert any("products/(?P<pk>" in rota for rota in rotas)  # o PADRÃO da rota (regex do router do DRF) vira rótulo...
    assert not any("999999" in rota for rota in rotas)  # ...e o ID cru, nunca (senão cada ID seria uma série nova)
