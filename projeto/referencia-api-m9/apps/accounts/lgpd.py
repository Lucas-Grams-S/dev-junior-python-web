"""Direitos do titular (LGPD, art. 18): acesso/portabilidade e anonimização. Regras de negócio, sem HTTP.

Decisão de projeto: NÃO apagamos o usuário que tem pedidos. O pedido é registro de uma venda, que precisa ser mantido por
obrigação legal/fiscal (LGPD, art. 7º, II). Em vez disso, ANONIMIZAMOS os dados pessoais e deixamos o pedido intacto."""
import logging

from django.db import transaction
from django.utils import timezone

seguranca = logging.getLogger("security")


def exportar_dados(user):
    """Tudo que guardamos SOBRE a pessoa, em formato estruturado (JSON). Nunca inclui o hash da senha nem tokens."""
    pedidos = []
    for o in user.orders.prefetch_related("items__product").select_related("payment"):
        pagamento = getattr(o, "payment", None)
        pedidos.append({
            "id": o.pk, "status": o.status, "total": str(o.total), "criado_em": o.created_at.isoformat(),
            "itens": [{"sku": i.product.sku, "produto": i.product.name, "quantidade": i.quantity, "preco_unitario": str(i.unit_price)} for i in o.items.all()],
            "pagamento": {"status": pagamento.status, "valor": str(pagamento.amount)} if pagamento else None,
        })
    carrinho = getattr(user, "cart", None)
    return {
        "gerado_em": timezone.now().isoformat(),
        "conta": {"usuario": user.username, "email": user.email, "nome": user.get_full_name(), "cadastrado_em": user.date_joined.isoformat(),
                  "ultimo_acesso": user.last_login.isoformat() if user.last_login else None},
        "pedidos": pedidos,
        "carrinho": [{"sku": i.product.sku, "quantidade": i.quantity} for i in carrinho.items.select_related("product")] if carrinho else [],
    }


@transaction.atomic
def anonimizar(user):
    """Remove os dados pessoais e desativa a conta, mantendo os pedidos (obrigação legal). Idempotente."""
    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
    if user.username.startswith("anonimo-"):
        return False
    user.username = f"anonimo-{user.pk}"
    user.email = ""
    user.first_name = user.last_name = ""
    user.is_active = False
    user.set_unusable_password()
    user.save()
    if hasattr(user, "cart"):
        user.cart.delete()                                          # carrinho não é registro fiscal
    for token in OutstandingToken.objects.filter(user=user):        # derruba as sessões abertas
        BlacklistedToken.objects.get_or_create(token=token)
    seguranca.info("titular_anonimizado user_id=%s", user.pk)
    return True
