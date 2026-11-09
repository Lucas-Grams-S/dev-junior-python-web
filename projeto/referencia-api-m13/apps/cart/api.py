from typing import TYPE_CHECKING, cast

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.schemas import ErrorSerializer

from . import services
from .models import CartItem
from .serializers import AddToCartSerializer, CartItemSerializer, CartItemUpdateSerializer, CartSerializer

if TYPE_CHECKING:
    from apps.accounts.models import User


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=CartSerializer, summary="Carrinho do usuário, com total")
    def get(self, request, *args, **kwargs):
        cart = services.get_cart(request.user)
        itens = cart.items.select_related("product__category").order_by("product__name")
        return Response(CartSerializer({"items": itens, "total": cart.total(), "count": cart.count()}).data)


@extend_schema_view(
    create=extend_schema(
        summary="Adiciona um item ao carrinho",
        request=AddToCartSerializer,
        responses={201: CartItemSerializer, 400: ErrorSerializer, 422: ErrorSerializer},
    ),
    partial_update=extend_schema(
        summary="Altera a quantidade (0 remove)",
        request=CartItemUpdateSerializer,
        responses={200: CartItemSerializer, 204: None, 422: ErrorSerializer},
    ),
    destroy=extend_schema(summary="Remove o item", responses={204: None}),
)
class CartItemViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["post", "patch", "delete", "options"]

    def get_queryset(self):  # sempre o carrinho DO usuário
        if getattr(self, "swagger_fake_view", False):  # geração do schema: sem usuário real
            return CartItem.objects.none()
        usuario = cast("User", self.request.user)  # IsAuthenticated garante que não é anônimo
        return CartItem.objects.filter(cart__user=usuario).select_related("product__category")

    def get_serializer_class(self):
        return AddToCartSerializer if self.action == "create" else CartItemUpdateSerializer

    def create(self, request, *args, **kwargs):
        ser = AddToCartSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        services.add_item(request.user, ser.validated_data["product"], ser.validated_data["quantity"])
        item = self.get_queryset().get(product_id=ser.validated_data["product"])
        return Response(
            CartItemSerializer(item).data, status=status.HTTP_201_CREATED, headers={"Location": f"/api/v1/cart/items/{item.pk}/"}
        )

    def partial_update(self, request, *args, **kwargs):
        item = self.get_object()
        ser = CartItemUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        services.set_quantity(request.user, item.product_id, ser.validated_data["quantity"])
        if ser.validated_data["quantity"] == 0:
            return Response(status=status.HTTP_204_NO_CONTENT)
        item.refresh_from_db()
        return Response(CartItemSerializer(item).data)

    def destroy(self, request, *args, **kwargs):
        item = self.get_object()
        services.remove_item(request.user, item.product_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
