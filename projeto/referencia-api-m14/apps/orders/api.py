from typing import TYPE_CHECKING, cast

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from config.pagination import NewestFirstCursorPagination
from config.schemas import ErrorSerializer

from . import selectors, services
from .filters import OrderFilter
from .idempotency import executar_idempotente
from .models import Order
from .notifications import notificar_pedido_criado
from .permissions import IsOwner
from .serializers import OrderSerializer

if TYPE_CHECKING:
    from apps.accounts.models import User


@extend_schema_view(
    list=extend_schema(summary="Meus pedidos (paginação por cursor)"),
    retrieve=extend_schema(summary="Detalhe de um pedido", responses={200: OrderSerializer, 404: ErrorSerializer}),
    create=extend_schema(
        summary="Finaliza o carrinho e cria o pedido",
        request=None,
        parameters=[
            OpenApiParameter(
                "Idempotency-Key",
                str,
                OpenApiParameter.HEADER,
                required=False,
                description=(
                    "UUID gerado pelo cliente por intenção de compra. Repetir a mesma chave devolve o mesmo pedido "
                    "(cabeçalho Idempotent-Replayed: true)."
                ),
            )
        ],
        responses={201: OrderSerializer, 422: ErrorSerializer},
    ),
)
class OrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = OrderFilter
    pagination_class = NewestFirstCursorPagination  # cursor: pedidos crescem sem parar
    ordering_fields = ["created_at", "total"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        usuario = cast("User", self.request.user)  # IsAuthenticated garante que não é anônimo
        return selectors.pedidos_visiveis(usuario)  # a REGRA de visibilidade mora no selector

    def create(self, request, *args, **kwargs):
        chave = request.headers.get("Idempotency-Key", "").strip()
        if not chave:
            status_http, corpo = self._criar(request)
            return Response(corpo, status=status_http, headers={"Location": f"/api/v1/orders/{corpo['id']}/"})
        if len(chave) > 64:
            raise ValidationError({"detail": "Idempotency-Key deve ter até 64 caracteres."})
        status_http, corpo, repetida = executar_idempotente(request.user, chave, lambda: self._criar(request))
        extra = {"Idempotent-Replayed": "true"} if repetida else {"Location": f"/api/v1/orders/{corpo['id']}/"}
        return Response(corpo, status=status_http, headers=extra)

    def _criar(self, request):
        order = services.create_order(request.user)
        notificar_pedido_criado(order)
        return status.HTTP_201_CREATED, OrderSerializer(order).data

    def get_permissions(self):
        if self.action == "cancel":  # cancelar: autenticado E dono do pedido
            return [IsAuthenticated(), IsOwner()]
        return super().get_permissions()

    @extend_schema(
        summary="Cancela o pedido e devolve o estoque",
        request=None,
        responses={200: OrderSerializer, 403: ErrorSerializer, 404: ErrorSerializer, 422: ErrorSerializer},
    )
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None, **kwargs):
        self.get_object()  # checa has_object_permission (403 se não for o dono)
        order = services.cancel_order(request.user, pk)
        return Response(OrderSerializer(order).data)
