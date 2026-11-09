from django.apps import AppConfig


class Config(AppConfig):
    name = "apps.accounts"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from . import receivers  # noqa: F401  (conecta os sinais)
