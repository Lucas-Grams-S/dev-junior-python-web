"""Métricas no formato Prometheus (aula 14.02): contagem e latência por ROTA (padrão da URL), nunca pelo caminho cru."""

import hmac
import os
import sys

from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseForbidden

# Modo multiprocesso (vários workers): a pasta PRECISA existir ANTES de importar o prometheus_client. Processos que não servem
# HTTP (migrate, celery) não têm a pasta: em vez de quebrar na importação, seguem sem o modo multiprocesso.
_pasta = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
if _pasta:
    try:
        os.makedirs(_pasta, exist_ok=True)
    except OSError:
        print(f"aviso: {_pasta} indisponível; métricas sem modo multiprocesso neste processo", file=sys.stderr)
        os.environ.pop("PROMETHEUS_MULTIPROC_DIR")

from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, Histogram, generate_latest, multiprocess  # noqa: E402

REQUISICOES = Counter("minishop_http_requests_total", "Requisições HTTP", ["method", "route", "status"])
LATENCIA = Histogram(
    "minishop_http_request_duration_seconds",
    "Latência das requisições HTTP",
    ["method", "route"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)
EM_ANDAMENTO = Gauge("minishop_http_requests_in_flight", "Requisições em andamento", multiprocess_mode="livesum")
CACHE = Counter("minishop_cache_requests_total", "Consultas ao cache do catálogo", ["result"])  # hit | miss | error | bypass


def rota(request) -> str:
    """O PADRÃO da URL (`api/<str:version>/products/<pk>/`), não `/api/v1/products/49/`: senão cada ID vira uma série nova."""
    match = getattr(request, "resolver_match", None)
    return match.route if match and match.route else "nao-resolvida"


def requisicao_iniciada():
    EM_ANDAMENTO.inc()


def observar_requisicao(request, status: int, duracao: float):
    EM_ANDAMENTO.dec()
    r = rota(request)
    REQUISICOES.labels(request.method, r, str(status)).inc()
    LATENCIA.labels(request.method, r).observe(duracao)


def metricas(request):
    """GET /metrics/ — exige `Authorization: Bearer <METRICS_TOKEN>`; sem o token configurado, o endpoint NÃO EXISTE (404)."""
    token = getattr(settings, "METRICS_TOKEN", "")
    if not token:
        raise Http404
    enviado = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not hmac.compare_digest(enviado.encode(), token.encode()):
        return HttpResponseForbidden("forbidden")
    if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):  # vários processos (uvicorn/gunicorn): agrega os arquivos de cada um
        registro = CollectorRegistry()
        multiprocess.MultiProcessCollector(registro)
        corpo = generate_latest(registro)
    else:
        corpo = generate_latest()
    return HttpResponse(corpo, content_type=CONTENT_TYPE_LATEST)
