"""Leituras (consultas) do app de pedidos: o 'R' do CRUD, sem efeitos colaterais."""
from .models import Order


def pedidos_visiveis(user):
    """Atendimento (permissão `view_order`) vê todos, só para leitura; o cliente vê apenas os seus (o alheio é 404)."""
    qs = Order.objects.prefetch_related("items__product")
    return qs if user.has_perm("orders.view_order") else qs.filter(user=user)
