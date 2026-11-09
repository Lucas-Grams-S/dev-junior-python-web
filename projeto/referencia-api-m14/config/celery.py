import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("minishop")
app.config_from_object("django.conf:settings", namespace="CELERY")  # lê as chaves CELERY_* do settings.py
app.autodiscover_tasks()  # procura apps/*/tasks.py
