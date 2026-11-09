from .celery import app as celery_app  # garante que o app Celery carrega junto com o Django

__all__ = ("celery_app",)
