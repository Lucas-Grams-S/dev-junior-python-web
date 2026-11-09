import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .security import AssinaturaInvalida, verificar
from .services import processar_evento

logger = logging.getLogger(__name__)
LIMITE_CORPO = 64 * 1024
FALHAS = {"n": 0}                                            # GANCHO DE DEMONSTRAÇÃO: simula o nosso servidor indisponível (ver webhook_demo.py)


@csrf_exempt                                                  # não há sessão/cookie: a autenticação é a ASSINATURA
@require_POST
def webhook_pagamentos(request):
    if FALHAS["n"] < int(__import__("os").environ.get("WEBHOOK_FAIL_FIRST", "0")):
        FALHAS["n"] += 1
        return JsonResponse({"detail": "indisponível"}, status=503)
    corpo = request.body                                      # BYTES brutos: a assinatura é sobre eles (nunca re-serialize o JSON)
    if len(corpo) > LIMITE_CORPO:
        return JsonResponse({"detail": "corpo grande demais", "code": "payload_too_large"}, status=413)
    try:
        verificar(settings.WEBHOOK_SECRET, corpo, request.headers.get("X-Signature"))
    except AssinaturaInvalida as e:
        logger.warning("webhook_rejeitado motivo=%s ip=%s", e, request.META.get("REMOTE_ADDR"))
        return JsonResponse({"detail": "assinatura inválida", "code": "invalid_signature"}, status=401)   # mensagem genérica
    try:
        evento = json.loads(corpo)
        evento["id"], evento["type"]
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"detail": "evento malformado", "code": "bad_event"}, status=400)
    resultado, detalhe = processar_evento(evento)
    logger.info("webhook evento=%s tipo=%s resultado=%s detalhe=%s", evento["id"], evento["type"], resultado, detalhe)
    return JsonResponse({"received": True, "result": resultado}, status=200)                             # 2xx RÁPIDO, mesmo p/ duplicata
