import django_filters

from .models import Product


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category__slug")  # ?category=audio
    price_min = django_filters.NumberFilter(field_name="price", lookup_expr="gte")  # ?price_min=50
    price_max = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    in_stock = django_filters.BooleanFilter(method="filter_in_stock")  # ?in_stock=true

    class Meta:
        model = Product
        fields = ["category", "price_min", "price_max", "in_stock"]

    def filter_in_stock(self, queryset, name, value):
        return queryset.filter(stock__gt=0) if value else queryset.filter(stock=0)
