"""Contexto da requisição (aula 14.01): ID de correlação, log de acesso estruturado e métricas."""

import logging
import re
import time
import uuid

from django.utils.deprecation import MiddlewareMixin

from .logging_json import request_id_var
from .metrics import observar_requisicao, requisicao_iniciada

acesso = logging.getLogger("minishop.access")
ID_VALIDO = re.compile(r"^[A-Za-z0-9._-]{8,64}$")  # aceita o ID do Nginx/cliente só se for "inofensivo" (anti log-injection)
SILENCIOSAS = ("/health/", "/metrics/")  # sondas a cada poucos segundos: nível DEBUG, para não afogar o log


class RequestContextMiddleware(MiddlewareMixin):
    def process_request(self, request):
        recebido = request.headers.get("X-Request-ID", "")
        request.request_id = recebido if ID_VALIDO.match(recebido) else uuid.uuid4().hex
        request._token_rid = request_id_var.set(request.request_id)
        request._inicio = time.perf_counter()
        requisicao_iniciada()

    def process_response(self, request, response):
        inicio = getattr(request, "_inicio", None)
        if inicio is None:  # process_request não rodou (outro middleware respondeu antes)
            return response
        duracao = time.perf_counter() - inicio
        user = getattr(request, "user", None)
        uid = str(getattr(user, "pk", "-")) if getattr(user, "is_authenticated", False) else "-"
        nivel = logging.DEBUG if request.path.startswith(SILENCIOSAS) else logging.INFO
        acesso.log(
            nivel,
            "%s %s %s",
            request.method,
            request.path,
            response.status_code,  # NUNCA a query string: no WebSocket e em links de e-mail ela carrega tokens
            extra={
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": round(duracao * 1000, 1),
                "user_id": uid,
            },
        )
        observar_requisicao(request, response.status_code, duracao)
        response["X-Request-ID"] = request.request_id
        token = getattr(request, "_token_rid", None)
        if token is not None:
            request_id_var.reset(token)  # a thread do servidor será reutilizada: não deixar o ID vazar para a próxima requisição
        return response
