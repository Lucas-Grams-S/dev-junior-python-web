import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .gateway import GatewayIndisponivel, obter_gateway
from .security import AssinaturaInvalida
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
        evento = obter_gateway().interpretar_webhook(request.headers, corpo)              # verifica a assinatura e TRADUZ o dialeto do provedor
    except AssinaturaInvalida as e:
        logger.warning("webhook_rejeitado motivo=%s ip=%s", e, request.META.get("REMOTE_ADDR"))
        return JsonResponse({"detail": "assinatura inválida", "code": "invalid_signature"}, status=401)   # mensagem genérica
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"detail": "evento malformado", "code": "bad_event"}, status=400)
    resultado, detalhe = processar_evento(evento)
    logger.info("webhook evento=%s tipo=%s resultado=%s detalhe=%s", evento.id, evento.tipo, resultado, detalhe)
    return JsonResponse({"received": True, "result": resultado}, status=200)                             # 2xx RÁPIDO, mesmo p/ duplicata


# ----------------------------------------------------------------------------- iniciar o pagamento (movido de orders)

from django.shortcuts import get_object_or_404  # noqa: E402
from drf_spectacular.utils import extend_schema  # noqa: E402
from rest_framework import status as http  # noqa: E402
from rest_framework.exceptions import ValidationError  # noqa: E402
from rest_framework.permissions import IsAuthenticated  # noqa: E402
from rest_framework.response import Response  # noqa: E402
from rest_framework.views import APIView  # noqa: E402

from apps.orders.models import Order  # noqa: E402
from config.errors import BusinessRuleError  # noqa: E402
from apps.orders.serializers import PagamentoIniciadoSerializer  # noqa: E402

from . import services  # noqa: E402


class PagarPedidoView(APIView):
    """POST /orders/{id}/pay/: vive em `payments` (quem depende de `orders` é `payments`, nunca o contrário)."""
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Inicia o pagamento (cria a cobrança no gateway) e devolve a referência", request=None,
                   responses={201: PagamentoIniciadoSerializer, 200: PagamentoIniciadoSerializer})
    def post(self, request, pk, **kwargs):
        order = get_object_or_404(Order.objects.filter(user=request.user), pk=pk)       # pedido alheio = 404
        if order.status != Order.Status.PENDING:
            raise ValidationError({"detail": "Só pedidos pendentes podem ser pagos."})
        existente = getattr(order, "payment", None)
        if existente:                                                                   # idempotente
            return Response({"payment_ref": existente.provider_ref, "amount": str(existente.amount), "status": existente.status})
        try:
            cobranca = obter_gateway().criar_cobranca(order.pk, order.total)               # o provedor é um DETALHE atrás da porta
        except GatewayIndisponivel as e:
            raise BusinessRuleError(detail=str(e), code="gateway_unavailable") from e
        p = services.criar_pagamento(order, cobranca.ref)
        return Response({"payment_ref": p.provider_ref, "amount": str(p.amount), "status": p.status}, status=http.HTTP_201_CREATED)
