from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from . import cache
from .models import Category, Product


@receiver([post_save, post_delete], sender=Product)
@receiver([post_save, post_delete], sender=Category)
def invalidar_catalogo(sender, **kwargs):
    # on_commit: só invalida DEPOIS que a mudança está gravada (senão outro processo recacheia o dado antigo no meio da transação)
    from django.db import transaction

    transaction.on_commit(cache.bump)
