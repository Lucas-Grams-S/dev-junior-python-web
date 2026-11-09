"""Sentry sem rede: um transporte falso captura o que SERIA enviado (módulo 14, aula 02)."""

import pytest
import sentry_sdk
from sentry_sdk.transport import Transport

from config.observability import init_sentry, scrub


class TransporteFalso(Transport):
    def __init__(self, options=None):
        super().__init__(options)
        self.eventos = []

    def capture_envelope(self, envelope):
        for item in envelope.items:
            if item.headers.get("type") == "event":
                self.eventos.append(item.payload.json)

    def flush(self, *a, **k):  # pragma: no cover
        pass


@pytest.fixture
def sentry(monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "https://chave@o0.ingest.sentry.io/1")
    monkeypatch.setenv("RELEASE", "sha-abc1234")
    t = TransporteFalso()
    assert init_sentry(transport=t) is True
    yield t
    sentry_sdk.init(dsn=None)  # desliga


def test_sem_dsn_nao_liga(monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    assert init_sentry() is False


def test_scrub_remove_segredos_da_requisicao():
    evento = {
        "request": {
            "headers": {"Authorization": "Bearer eyJ...", "Cookie": "sessionid=1", "User-Agent": "curl", "X-Api-Key": "k"},
            "cookies": {"sessionid": "1"},
            "data": {"username": "ana", "password": "dev-somente-local-123"},
            "query_string": "token=SEGREDO",
        },
        "extra": {"senha": "x", "pedido": 7},
    }
    limpo = scrub(evento, {})
    req = limpo["request"]
    assert req["headers"] == {"Authorization": "[Filtered]", "Cookie": "[Filtered]", "User-Agent": "curl", "X-Api-Key": "[Filtered]"}
    assert "cookies" not in req and "data" not in req and req["query_string"] == "[Filtered]"
    assert limpo["extra"] == {"senha": "[Filtered]", "pedido": 7}


def test_excecao_nao_tratada_chega_ao_sentry_com_release_e_sem_segredos(sentry, monkeypatch, settings):
    def explode(*a, **k):
        raise RuntimeError("falha de teste")

    monkeypatch.setattr("config.metrics.generate_latest", explode)  # uma falha real, dentro de uma view real do projeto
    settings.METRICS_TOKEN = "t"
    from django.test import Client

    r = Client(raise_request_exception=False).get(
        "/metrics/?token=SEGREDO", headers={"Authorization": "Bearer t", "Cookie": "sessionid=abc", "X-Api-Key": "chave-xyz"}
    )
    assert r.status_code == 500
    sentry_sdk.flush()
    (ev,) = sentry.eventos
    assert ev["release"] == "sha-abc1234" and ev["exception"]["values"][0]["type"] == "RuntimeError"
    texto = str(ev)
    for segredo in ("SEGREDO", "sessionid=abc", "chave-xyz"):
        assert segredo not in texto


@pytest.mark.django_db
def test_erro_dentro_de_view_do_drf_tambem_chega_ao_sentry(sentry, monkeypatch):
    """O handler de erros do projeto devolve JSON para erros de API, mas NÃO pode engolir os inesperados (500)."""

    def explode(self):
        raise ZeroDivisionError("bug na lista de produtos")

    monkeypatch.setattr("apps.catalog.api.ProductViewSet.get_queryset", explode)
    from django.test import Client

    r = Client(raise_request_exception=False).get("/api/v1/products/")
    assert r.status_code == 500 and r.json()["code"] == "server_error"
    sentry_sdk.flush()
    assert [e["exception"]["values"][0]["type"] for e in sentry.eventos] == ["ZeroDivisionError"]
