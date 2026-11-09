from django.core.management.base import BaseCommand

from apps.orders.tasks import reenviar_emails_falhos


class Command(BaseCommand):
    help = "Recoloca na fila os e-mails que falharam (depois de corrigir a causa)."

    def handle(self, *args, **opts):
        n = reenviar_emails_falhos()  # UMA implementação, duas portas de entrada (tarefa agendada e comando)
        self.stdout.write(f"{n} e-mail(s) reenfileirado(s)")
