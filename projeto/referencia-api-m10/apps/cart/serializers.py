from rest_framework import serializers

from apps.cart.services import QUANTIDADE_MAXIMA
from apps.catalog.serializers import ProductSerializer

from .models import CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    unit_price = serializers.DecimalField(source="product.price", max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity", "unit_price", "subtotal"]


class CartSerializer(serializers.Serializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    count = serializers.IntegerField(read_only=True)


class AddToCartSerializer(serializers.Serializer):
    product = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=QUANTIDADE_MAXIMA, default=1)


class CartItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=0, max_value=QUANTIDADE_MAXIMA)
