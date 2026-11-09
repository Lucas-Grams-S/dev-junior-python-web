import csv

from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view

from .models import Order

# Planilhas (Excel, Sheets, LibreOffice) executam células que começam com estes caracteres como FÓRMULA (CSV injection).
PREFIXOS_DE_FORMULA = ("=", "+", "-", "@", "\t", "\r")


def celula_segura(valor: object) -> str:
    """Texto controlado pelo usuário (nome, e-mail) é neutralizado com um apóstrofo inicial."""
    texto = str(valor)
    return "'" + texto if texto.startswith(PREFIXOS_DE_FORMULA) else texto


@extend_schema(summary="Exporta pedidos em CSV", responses={(200, "text/csv"): OpenApiTypes.STR})
@api_view(["GET"])
def exportar_pedidos(request, **kwargs):
    resposta = HttpResponse(content_type="text/csv")
    escritor = csv.writer(resposta)
    escritor.writerow(["id", "cliente", "email", "total", "status"])
    pedidos = Order.objects.filter(user=request.user).select_related("user")
    for pedido in pedidos.iterator(chunk_size=500):  # lê em blocos: não carrega tudo na memória
        escritor.writerow([pedido.id, celula_segura(pedido.user.username), celula_segura(pedido.user.email), pedido.total, pedido.status])
    return resposta
