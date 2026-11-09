from django_filters.rest_framework import DjangoFilterBackend
from django.db import IntegrityError, transaction
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import services
from config.pagination import NewestFirstCursorPagination

from config.schemas import ErrorSerializer

from .filters import OrderFilter
from .models import IdempotencyKey, Order
from .notifications import notificar_pedido_criado
from .permissions import IsOwner
from .serializers import OrderSerializer, PagamentoIniciadoSerializer


@extend_schema_view(
    list=extend_schema(summary="Meus pedidos (paginação por cursor)"),
    retrieve=extend_schema(summary="Detalhe de um pedido", responses={200: OrderSerializer, 404: ErrorSerializer}),
    create=extend_schema(summary="Finaliza o carrinho e cria o pedido", request=None,
                         parameters=[OpenApiParameter("Idempotency-Key", str, OpenApiParameter.HEADER, required=False,
                                                      description="UUID gerado pelo cliente por intenção de compra. Repetir a mesma chave devolve o mesmo pedido (cabeçalho Idempotent-Replayed: true).")],
                         responses={201: OrderSerializer, 422: ErrorSerializer}),
)
class OrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = OrderFilter
    pagination_class = NewestFirstCursorPagination                 # cursor: pedidos crescem sem parar
    ordering_fields = ["created_at", "total"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        qs = Order.objects.prefetch_related("items__product")
        if self.request.user.has_perm("orders.view_order"):         # atendimento/superusuário: vê todos (só leitura)
            return qs
        return qs.filter(user=self.request.user)                    # cliente: só os seus; o alheio é 404

    def create(self, request, *args, **kwargs):
        chave = request.headers.get("Idempotency-Key", "").strip()
        if not chave:
            return self._criar(request)
        if len(chave) > 64:
            raise ValidationError({"detail": "Idempotency-Key deve ter até 64 caracteres."})
        anterior = IdempotencyKey.objects.filter(user=request.user, key=chave).first()
        if anterior:                                                       # repetição: devolve o resultado guardado
            return Response(anterior.response_body, status=anterior.response_status, headers={"Idempotent-Replayed": "true"})
        try:
            with transaction.atomic():                                     # pedido + registro da chave: tudo ou nada
                resposta = self._criar(request)
                IdempotencyKey.objects.create(user=request.user, key=chave, response_status=resposta.status_code,
                                              response_body=resposta.data)
            return resposta
        except IntegrityError:                                             # outra requisição com a mesma chave ganhou a corrida
            anterior = IdempotencyKey.objects.get(user=request.user, key=chave)
            return Response(anterior.response_body, status=anterior.response_status, headers={"Idempotent-Replayed": "true"})

    def _criar(self, request):
        order = services.create_order(request.user)
        notificar_pedido_criado(order)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED, headers={"Location": f"/api/v1/orders/{order.pk}/"})

    def get_permissions(self):
        if self.action in ("cancel", "pay"):                          # cancelar/pagar: autenticado E dono do pedido
            return [IsAuthenticated(), IsOwner()]
        return super().get_permissions()

    @extend_schema(summary="Inicia o pagamento (cria a cobrança no gateway) e devolve a referência", request=None,
                   responses={201: PagamentoIniciadoSerializer, 200: PagamentoIniciadoSerializer, 422: ErrorSerializer})
    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None, **kwargs):
        from apps.payments import services as pagamentos
        order = self.get_object()
        if order.status != Order.Status.PENDING:
            raise ValidationError({"detail": "Só pedidos pendentes podem ser pagos."})
        existente = getattr(order, "payment", None)
        if existente:
            return Response({"payment_ref": existente.provider_ref, "amount": str(existente.amount), "status": existente.status})
        ref = "pay_" + __import__("uuid").uuid4().hex[:16]                 # no real: a referência vem da API do gateway (módulo 8: Adapter)
        p = pagamentos.criar_pagamento(order, ref)
        return Response({"payment_ref": p.provider_ref, "amount": str(p.amount), "status": p.status}, status=status.HTTP_201_CREATED)

    @extend_schema(summary="Cancela o pedido e devolve o estoque", request=None,
                   responses={200: OrderSerializer, 403: ErrorSerializer, 404: ErrorSerializer, 422: ErrorSerializer})
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None, **kwargs):
        self.get_object()                                         # checa has_object_permission (403 se não for o dono)
        order = services.cancel_order(request.user, pk)
        return Response(OrderSerializer(order).data)
