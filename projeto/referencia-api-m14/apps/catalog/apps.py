from django.apps import AppConfig


class Config(AppConfig):
    name = "apps.catalog"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from . import signals  # noqa: F401  (registra a invalidação do cache do catálogo)
