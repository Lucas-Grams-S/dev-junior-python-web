from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.orders.models import IdempotencyKey


class Command(BaseCommand):
    help = "Apaga chaves de idempotência com mais de 24 horas."

    def handle(self, *args, **opts):
        limite = timezone.now() - timedelta(hours=24)
        apagadas, _ = IdempotencyKey.objects.filter(created_at__lt=limite).delete()
        self.stdout.write(f"{apagadas} chave(s) apagada(s)")
