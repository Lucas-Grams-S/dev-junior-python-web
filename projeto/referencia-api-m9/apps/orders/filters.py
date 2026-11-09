import django_filters
from .models import Order


class OrderFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Order.Status.choices)

    class Meta:
        model = Order
        fields = ["status"]
