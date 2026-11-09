"""Health checks (aula 14.01): LIVENESS (o processo está vivo?) × READINESS (consegue atender? banco e cache respondem?)."""

import logging
import time
import uuid

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


@never_cache
@require_GET
def liveness(request):
    """Não toca em NADA externo: se isto falha, o processo está travado e reiniciá-lo faz sentido."""
    return JsonResponse({"status": "ok"})


def _banco():
    with connection.cursor() as c:
        c.execute("SELECT 1")
        c.fetchone()


def _cache():
    chave = f"health:{uuid.uuid4().hex}"
    cache.set(chave, "1", 5)
    if cache.get(chave) != "1":
        raise RuntimeError("cache não devolveu o valor gravado")
    cache.delete(chave)


@never_cache
@require_GET
def readiness(request):
    """200 se banco e cache respondem; 503 caso contrário. O corpo NÃO vaza detalhes de erro (eles vão para o log)."""
    resultado, ok = {}, True
    for nome, teste in (("database", _banco), ("cache", _cache)):
        inicio = time.perf_counter()
        try:
            teste()
            resultado[nome] = {"status": "ok", "ms": round((time.perf_counter() - inicio) * 1000, 1)}
        except Exception:
            ok = False
            logger.exception("readiness_failed check=%s", nome)  # o traceback fica no log/Sentry, não na resposta
            resultado[nome] = {"status": "error"}
    return JsonResponse({"status": "ok" if ok else "error", "checks": resultado}, status=200 if ok else 503)
