from django.apps import AppConfig


class Config(AppConfig):
    name = "apps.realtime"

    def ready(self):
        from . import receivers  # noqa: F401  (conecta o receptor ao sinal)
