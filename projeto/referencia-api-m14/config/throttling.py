"""Limitação de taxa que FALHA ABERTA quando o cache cai (aula 14.03).

O DRF guarda os contadores no cache. Se o Redis cair, o `cache.get` levanta exceção DENTRO da checagem de taxa e CADA requisição vira 500:
um componente "opcional" derrubaria a API inteira. Aqui, se o cache falhar, a requisição passa (e o erro é registrado).
Troca consciente: durante a queda, a proteção de volume some.
O limite de LOGIN fica estrito (`ThrottledTokenView`): sem cache, o login falha.
"""

import logging

from rest_framework.exceptions import APIException
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle, UserRateThrottle

logger = logging.getLogger(__name__)


class _FalhaAberta:
    def allow_request(self, request, view):
        try:
            return super().allow_request(request, view)  # type: ignore[misc]  # mixin: `super()` é o SimpleRateThrottle
        except Exception:
            logger.warning("throttle_cache_unavailable scope=%s", getattr(self, "scope", "?"), exc_info=True)
            return True


class AnonThrottleFalhaAberta(_FalhaAberta, AnonRateThrottle):
    pass


class UserThrottleFalhaAberta(_FalhaAberta, UserRateThrottle):
    pass


class ServicoIndisponivel(APIException):
    status_code = 503
    default_detail = "Serviço temporariamente indisponível. Tente novamente em instantes."
    default_code = "service_unavailable"


class LoginThrottleFechado(ScopedRateThrottle):
    """Limite de LOGIN: FALHA FECHADA. Sem o contador não dá para limitar tentativas; melhor recusar com 503 do que ficar sem proteção."""

    def allow_request(self, request, view):
        try:
            return super().allow_request(request, view)
        except Exception as erro:
            logger.error("login_throttle_cache_unavailable", exc_info=True)
            raise ServicoIndisponivel() from erro
