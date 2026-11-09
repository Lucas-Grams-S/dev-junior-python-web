import re

from rest_framework import serializers

from .models import Category, Product

SKU_RE = re.compile(r"^[A-Z]{3}-\d{3}$")


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)  # leitura: objeto aninhado
    category_slug = serializers.SlugRelatedField(  # escrita: só o slug
        source="category", slug_field="slug", queryset=Category.objects.all(), write_only=True
    )
    in_stock = serializers.SerializerMethodField()  # campo calculado, só leitura
    image_url = serializers.SerializerMethodField()  # URL da imagem (assinada e temporária quando o bucket é privado)

    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "name",
            "slug",
            "description",
            "price",
            "stock",
            "in_stock",
            "image_url",
            "is_active",
            "category",
            "category_slug",
            "created_at",
        ]
        read_only_fields = ["slug", "created_at"]

    def get_in_stock(self, obj) -> bool:
        return obj.stock > 0

    def get_image_url(self, obj) -> str | None:
        return obj.image.url if obj.image else None

    def validate_sku(self, value):
        value = value.strip().upper()
        if not SKU_RE.match(value):
            raise serializers.ValidationError("Use o formato AAA-123 (3 letras, hífen, 3 números).")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("O preço deve ser maior que zero.")
        return value

    def validate(self, attrs):  # regra entre campos
        if attrs.get("is_active") is False and attrs.get("stock", 0) > 0:
            raise serializers.ValidationError("Não desative um produto que ainda tem estoque.")
        return attrs


MAX_IMAGE_BYTES = 2 * 1024 * 1024  # 2 MB
IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


class ProductImageSerializer(serializers.Serializer):
    """Upload de imagem: valida tamanho e FORMATO REAL (o Pillow abre o arquivo; a extensão do nome não conta)."""

    image = serializers.ImageField()

    def validate_image(self, f):
        if f.size > MAX_IMAGE_BYTES:
            raise serializers.ValidationError("A imagem deve ter no máximo 2 MB.")
        if getattr(f.image, "format", None) not in IMAGE_FORMATS:
            raise serializers.ValidationError("Formato não aceito (use JPEG, PNG ou WebP).")
        return f
