from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "lab-only-not-secret"
DEBUG = True
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions",
    "django.contrib.messages", "django.contrib.staticfiles",
    "corsheaders", "rest_framework", "drf_spectacular", "django_filters", "rest_framework_simplejwt", "rest_framework_simplejwt.token_blacklist",
    "apps.accounts", "apps.catalog", "apps.cart", "apps.orders", "apps.payments", "apps.realtime", "channels",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "corsheaders.middleware.CorsMiddleware",   # CORS antes do CommonMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware", "django.contrib.messages.middleware.MessageMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True,
              "OPTIONS": {"context_processors": ["django.template.context_processors.request", "django.contrib.auth.context_processors.auth",
                                                 "django.contrib.messages.context_processors.messages"]}}]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
AUTH_USER_MODEL = "accounts.User"
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "UTC"
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],   # negar por padrão
    "EXCEPTION_HANDLER": "config.errors.api_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_VERSION": "v1",
    "ALLOWED_VERSIONS": ["v1"],
    "DEFAULT_PAGINATION_CLASS": "config.pagination.StandardPagination",
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.AnonRateThrottle", "rest_framework.throttling.UserRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"anon": "100/hour", "user": "1000/hour", "login": "5/min"},
}

from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,          # cada refresh devolve um refresh NOVO...
    "BLACKLIST_AFTER_ROTATION": True,       # ...e o antigo deixa de valer
    "AUTH_HEADER_TYPES": ("Bearer",),
    "UPDATE_LAST_LOGIN": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "MiniShop API",
    "DESCRIPTION": "API do MiniShop: catálogo, carrinho e pedidos. Autenticação por JWT (Bearer).",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
}

# --- CORS (aula 11) ---
import os

CORS_ALLOWED_ORIGINS = [o for o in os.environ.get("CORS_ALLOWED_ORIGINS", "http://127.0.0.1:8200").split(",") if o]
CORS_URLS_REGEX = r"^/api/.*$"                         # só a API fala com outras origens (o /admin/ não)
CORS_ALLOW_CREDENTIALS = False                         # JWT vai no cabeçalho; sem cookies entre origens
from corsheaders.defaults import default_headers

CORS_ALLOW_HEADERS = (*default_headers, "idempotency-key")          # cabeçalho PERSONALIZADO do front precisa ser liberado no preflight
CORS_EXPOSE_HEADERS = ["Location", "Retry-After", "Idempotent-Replayed"]   # cabeçalhos que o JavaScript pode LER na resposta
CORS_PREFLIGHT_MAX_AGE = 600                           # o navegador reaproveita o preflight por 10 min

# --- Celery e e-mail (aula 7.06) ---
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6390/0")
CELERY_RESULT_BACKEND = None                          # não guardamos resultados: a tarefa tem efeito (e-mail), não valor
CELERY_TASK_IGNORE_RESULT = True
CELERY_TASK_SERIALIZER = "json"                       # só dados simples: ids, textos (nunca objetos do ORM)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "UTC"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
EMAIL_BACKEND = "apps.orders.email_backend.SmtpLentoEmailBackend"
EMAIL_SIMULATED_DELAY = float(os.environ.get("EMAIL_SIMULATED_DELAY", "0.8"))   # segundos que o "SMTP" demora
EMAIL_OUTBOX_FILE = os.environ.get("EMAIL_OUTBOX_FILE", str(BASE_DIR / "outbox.jsonl"))
ORDER_EMAIL_MODE = os.environ.get("ORDER_EMAIL_MODE", "async")    # "sync" | "async" | "off"
DEFAULT_FROM_EMAIL = "MiniShop <nao-responda@minishop.local>"

# --- Agendamento (aula 7.08): quem LÊ isto é o `celery beat` ---
from celery.schedules import crontab  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    "limpar-chaves-de-idempotencia": {"task": "orders.limpar_chaves_de_idempotencia", "schedule": crontab(minute=0, hour=3)},   # todo dia, 03:00 UTC
    "cancelar-pedidos-pendentes": {"task": "orders.cancelar_pedidos_pendentes_antigos", "schedule": crontab(minute="*/15")},   # a cada 15 min
    "reenviar-emails-falhos": {"task": "orders.reenviar_emails_falhos", "schedule": crontab(minute=5)},                          # toda hora, no minuto 5
}
if os.environ.get("BEAT_DEMO") == "cron":                               # demonstração: o mesmo "pulso", mas como crontab (todo minuto)
    CELERY_BEAT_SCHEDULE = {"pulso": {"task": "orders.batimento", "schedule": crontab(minute="*")}}
elif os.environ.get("BEAT_DEMO"):                                       # só para a demonstração da aula: um "pulso" a cada 2 s
    CELERY_BEAT_SCHEDULE = {"pulso": {"task": "orders.batimento", "schedule": 2.0}}

# --- Webhooks (aula 7.09) ---
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "whsec_lab_apenas_para_estudo")   # em produção: variável de ambiente, longa e aleatória

# --- WebSockets (aula 7.10): a camada de canais precisa ser COMPARTILHADA entre processos (Redis) ---
ASGI_APPLICATION = "config.asgi.application"
CHANNEL_LAYERS = {"default": {"BACKEND": "channels_redis.core.RedisChannelLayer",
                              "CONFIG": {"hosts": [(os.environ.get("REDIS_HOST", "127.0.0.1"), int(os.environ.get("REDIS_PORT", "6390")))]}}}
