from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import AllowAny, DjangoModelPermissionsOrAnonReadOnly

from .filters import ProductFilter
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer


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

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.has_perm("catalog.change_product"):  # equipe vê inativos; público só os ativos
            return qs
        return qs.filter(is_active=True)
