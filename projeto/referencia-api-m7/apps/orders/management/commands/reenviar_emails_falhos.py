from django.core.management.base import BaseCommand

from apps.orders.models import EmailLog
from apps.orders.tasks import send_order_confirmation_email


class Command(BaseCommand):
    help = "Recoloca na fila os e-mails que falharam (depois de corrigir a causa)."

    def handle(self, *args, **opts):
        ids = list(EmailLog.objects.filter(status=EmailLog.Status.FAILED).values_list("order_id", flat=True))
        EmailLog.objects.filter(order_id__in=ids, status=EmailLog.Status.FAILED).update(status=EmailLog.Status.PENDING, attempts=0)
        for i in ids:
            send_order_confirmation_email.delay(i)
        self.stdout.write(f"{len(ids)} e-mail(s) reenfileirado(s)")
