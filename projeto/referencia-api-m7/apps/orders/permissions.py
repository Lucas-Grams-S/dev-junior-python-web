from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Autorização POR OBJETO: só o dono. Roda em get_object() (detalhe e ações), nunca na lista."""
    message = "Você não é o dono deste pedido."

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id
