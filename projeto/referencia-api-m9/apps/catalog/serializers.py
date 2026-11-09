import re

from rest_framework import serializers

from .models import Category, Product

SKU_RE = re.compile(r"^[A-Z]{3}-\d{3}$")


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)                                   # leitura: objeto aninhado
    category_slug = serializers.SlugRelatedField(                                   # escrita: só o slug
        source="category", slug_field="slug", queryset=Category.objects.all(), write_only=True)
    in_stock = serializers.SerializerMethodField()                                   # campo calculado, só leitura

    class Meta:
        model = Product
        fields = ["id", "sku", "name", "slug", "description", "price", "stock", "in_stock",
                  "is_active", "category", "category_slug", "created_at"]
        read_only_fields = ["slug", "created_at"]

    def get_in_stock(self, obj) -> bool:
        return obj.stock > 0

    def validate_sku(self, value):
        value = value.strip().upper()
        if not SKU_RE.match(value):
            raise serializers.ValidationError("Use o formato AAA-123 (3 letras, hífen, 3 números).")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("O preço deve ser maior que zero.")
        return value

    def validate(self, attrs):                                                       # regra entre campos
        if attrs.get("is_active") is False and attrs.get("stock", 0) > 0:
            raise serializers.ValidationError("Não desative um produto que ainda tem estoque.")
        return attrs
