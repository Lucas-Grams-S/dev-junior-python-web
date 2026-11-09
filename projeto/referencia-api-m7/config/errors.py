import logging

from django.http import Http404, JsonResponse
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler as drf_exception_handler

from apps.cart.services import CartError
from apps.orders.services import EmptyCartError, OrderError, StockError

logger = logging.getLogger(__name__)


class BusinessRuleError(APIException):
    """Dados válidos, mas a regra de negócio impede a operação: 422."""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "A operação viola uma regra de negócio."
    default_code = "business_rule"


CODIGOS = {EmptyCartError: "empty_cart", StockError: "insufficient_stock"}


def api_exception_handler(exc, context):
    """Formato único: erros de campo ficam como {"campo": [..]}; todo o resto vira {"detail", "code"}."""
    if isinstance(exc, (CartError, OrderError)):                      # exceções do domínio → 422
        codigo = next((c for tipo, c in CODIGOS.items() if isinstance(exc, tipo)), "business_rule")
        exc = BusinessRuleError(detail=str(exc), code=codigo)
    elif isinstance(exc, Http404):
        exc = _NaoEncontrado()
    response = drf_exception_handler(exc, context)
    if response is not None and isinstance(response.data, dict) and "detail" in response.data:
        detalhe = response.data["detail"]
        response.data = {"detail": str(detalhe), "code": getattr(detalhe, "code", "error")}
    return response


from rest_framework.exceptions import NotFound  # noqa: E402


class _NaoEncontrado(NotFound):
    default_detail = "Não encontrado."


def json_500(request, *args, **kwargs):
    """handler500: erro inesperado também em JSON para quem chama /api/ (sem vazar detalhes)."""
    logger.exception("unhandled_error path=%s", request.path)
    if request.path.startswith("/api/"):
        return JsonResponse({"detail": "Erro interno. Tente novamente mais tarde.", "code": "server_error"}, status=500)
    from django.views.defaults import server_error
    return server_error(request, *args, **kwargs)
