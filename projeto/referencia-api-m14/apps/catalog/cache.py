"""Cache do catálogo (aula 14.03): chaves VERSIONADAS, TTL curto e falha aberta.

Ideia: toda chave de resposta carrega o número da versão do catálogo. Mudou um produto? `bump()` incrementa a versão e TODAS as chaves
antigas passam a ser inalcançáveis (O(1), sem apagar uma a uma); elas morrem sozinhas pelo TTL.
"""

import hashlib
import logging

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)
VERSION_KEY = "catalog:version"


def _contar(resultado: str):
    try:  # a métrica é opcional: o módulo de cache não pode depender do módulo de métricas para funcionar
        from config.metrics import CACHE

        CACHE.labels(resultado).inc()
    except Exception:  # noqa: S110
        pass


def versao() -> int:
    try:
        v = cache.get(VERSION_KEY)
        if v is None:
            cache.add(VERSION_KEY, 1, None)  # `add` não sobrescreve: se outro processo criou antes, vale o dele
            v = cache.get(VERSION_KEY) or 1
        return int(v)
    except Exception:
        logger.warning("catalog_cache_version_unavailable", exc_info=True)
        return 0


def bump() -> None:
    """Invalida o catálogo inteiro. Chamado por signals de Product/Category e pelas mudanças de ESTOQUE (que usam `.update()`)."""
    try:
        cache.incr(VERSION_KEY)
    except ValueError:  # a chave ainda não existe
        cache.add(VERSION_KEY, 2, None)
    except Exception:
        logger.warning("catalog_cache_bump_failed", exc_info=True)


def chave(request, formato: str) -> str:
    bruto = f"{request.path}?{'&'.join(sorted(request.META.get('QUERY_STRING', '').split('&')))}|{formato}"
    return f"catalog:v{versao()}:{hashlib.sha256(bruto.encode()).hexdigest()[:32]}"


def obter(k: str):
    try:
        valor = cache.get(k)
    except Exception:
        logger.warning("catalog_cache_get_failed", exc_info=True)
        _contar("error")
        return None  # falha ABERTA: se o Redis cair, o site continua (mais lento), não fica fora do ar
    _contar("hit" if valor is not None else "miss")
    return valor


def gravar(k: str, valor, ttl: int | None = None) -> None:
    try:
        cache.set(k, valor, ttl if ttl is not None else getattr(settings, "CATALOG_CACHE_TTL", 60))
    except Exception:
        logger.warning("catalog_cache_set_failed", exc_info=True)
