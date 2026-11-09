"""Leituras (consultas) do app de pedidos: o 'R' do CRUD, sem efeitos colaterais."""

from typing import TYPE_CHECKING

from django.db.models import QuerySet

from .models import Order

if TYPE_CHECKING:
    from apps.accounts.models import User


def pedidos_visiveis(user: "User") -> "QuerySet[Order]":
    """Atendimento (permissão `view_order`) vê todos, só para leitura; o cliente vê apenas os seus (o alheio é 404)."""
    qs = Order.objects.prefetch_related("items__product")
    return qs if user.has_perm("orders.view_order") else qs.filter(user=user)
