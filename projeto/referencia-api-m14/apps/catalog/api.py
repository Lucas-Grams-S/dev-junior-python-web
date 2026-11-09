import json

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, DjangoModelPermissionsOrAnonReadOnly
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from . import cache
from .filters import ProductFilter
from .models import Category, Product
from .serializers import CategorySerializer, ProductImageSerializer, ProductSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]  # catálogo público, somente leitura


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category")  # evita N+1 na lista
    serializer_class = ProductSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]  # leitura pública; escrita exige catalog.add/change/delete_product
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name", "sku", "description"]  # ?search=mouse  (icontains em OR)
    ordering_fields = ["price", "name", "created_at"]  # lista permitida: ?ordering=-price
    ordering = ["name"]  # padrão

    def _com_cache(self, request, producao, *args, **kwargs):
        """Cache só para ANÔNIMOS em GET (a resposta é igual para todos). Logados (inclusive a equipe, que vê inativos) passam direto."""
        if request.method != "GET" or request.user.is_authenticated:
            resposta = producao(request, *args, **kwargs)
            resposta["X-Cache"] = "BYPASS"
            return resposta
        k = cache.chave(request, request.accepted_renderer.format)
        guardado = cache.obter(k)
        if guardado is not None:
            resposta = Response(guardado)
            resposta["X-Cache"] = "HIT"
            return resposta
        resposta = producao(request, *args, **kwargs)
        if resposta.status_code == 200:
            cache.gravar(k, json.loads(JSONRenderer().render(resposta.data)))  # dados simples (sem o serializer preso ao ReturnDict)
        resposta["X-Cache"] = "MISS"
        return resposta

    def list(self, request, *args, **kwargs):
        return self._com_cache(request, super().list, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return self._com_cache(request, super().retrieve, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.has_perm("catalog.change_product"):  # equipe vê inativos; público só os ativos
            return qs
        return qs.filter(is_active=True)

    @action(detail=True, methods=["post", "delete"], url_path="image", parser_classes=[MultiPartParser])
    def image(self, request, pk=None, **kwargs):  # `version` chega por kwargs (URLPathVersioning)
        """POST (multipart, campo `image`) envia/substitui a imagem; DELETE remove. Exige catalog.change_product."""
        produto = self.get_object()
        if request.method == "DELETE":
            if produto.image:
                produto.image.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        ser = ProductImageSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        if produto.image:
            produto.image.delete(save=False)  # não deixa arquivo órfão no bucket
        produto.image.save(f"{produto.sku.lower()}.{ser.validated_data['image'].image.format.lower()}", ser.validated_data["image"])
        return Response(ProductSerializer(produto, context={"request": request}).data)
