from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.lgpd import anonimizar


class Command(BaseCommand):
    help = "Anonimiza um titular (direito à eliminação/anonimização, LGPD art. 18, IV e VI). Mantém os pedidos por obrigação legal."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, username, **options):
        try:
            user = get_user_model().objects.get(username=username)
        except get_user_model().DoesNotExist:
            raise CommandError("Titular não encontrado.") from None
        self.stdout.write("anonimizado" if anonimizar(user) else "já estava anonimizado")
