import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.lgpd import exportar_dados


class Command(BaseCommand):
    help = "Exporta os dados de um titular em JSON (direito de acesso/portabilidade, LGPD art. 18, II e V)."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, username, **options):
        try:
            user = get_user_model().objects.get(username=username)
        except get_user_model().DoesNotExist:
            raise CommandError("Titular não encontrado.") from None
        self.stdout.write(json.dumps(exportar_dados(user), ensure_ascii=False, indent=2))
