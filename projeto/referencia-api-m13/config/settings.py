import os
import secrets
from datetime import timedelta
from pathlib import Path
from typing import Any

from corsheaders.defaults import default_headers
from django.core.exceptions import ImproperlyConfigured

from config.envconf import database_from_url, env_bool, env_list, env_or_file

BASE_DIR = Path(__file__).resolve().parent.parent

# Fator III (config no ambiente). Padrão SEGURO: sem DEBUG_MODE explícito, DEBUG é False e a chave é obrigatória.
DEBUG = env_bool("DEBUG", False)
SECRET_KEY = env_or_file("SECRET_KEY")  # ou SECRET_KEY_FILE=/run/secrets/... (aula 11.04)
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = secrets.token_urlsafe(50)  # só em DEBUG: chave nova a cada processo (sessões de dev não sobrevivem ao reinício)
    else:
        raise ImproperlyConfigured("SECRET_KEY é obrigatória quando DEBUG=False (defina a variável de ambiente).")
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", ["*"] if DEBUG else [])
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    "django_filters",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "apps.accounts",
    "apps.catalog",
    "apps.cart",
    "apps.orders",
    "apps.payments",
    "apps.realtime",
    "channels",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # CORS antes do CommonMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",  # X-Frame-Options em TODOS os ambientes
    "config.security_headers.SecurityHeadersMiddleware",  # CSP e Permissions-Policy (aula 9.06)
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
# Variável vazia (comum em CI/Compose) conta como não definida.
DATABASES = {"default": database_from_url(os.environ.get("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'db.sqlite3'}")}
AUTH_USER_MODEL = "accounts.User"
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "UTC"
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = Path(os.environ.get("STATIC_ROOT", BASE_DIR / "staticfiles"))  # `collectstatic` copia os estáticos para cá (aula 11.02)
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Mídia (aula 13.06): disco local por padrão; S3 quando AWS_STORAGE_BUCKET_NAME está definida ---
MEDIA_URL = "media/"
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", BASE_DIR / "media"))
STORAGES: dict[str, Any] = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
if os.environ.get("AWS_STORAGE_BUCKET_NAME"):
    # Credenciais: NUNCA aqui. Na EC2 vêm do PAPEL (instance profile) pela cadeia padrão do boto3 (aula 13.03).
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": os.environ["AWS_STORAGE_BUCKET_NAME"],
            "region_name": os.environ.get("AWS_S3_REGION_NAME", "sa-east-1"),
            "endpoint_url": os.environ.get("AWS_S3_ENDPOINT_URL") or None,  # só para testes locais (moto/MinIO)
            "signature_version": "s3v4",  # obrigatória nas regiões novas; o padrão antigo (v2) gera URLs rejeitadas
            "default_acl": None,  # bucket privado, sem ACL por objeto
            "querystring_auth": True,  # URLs assinadas e temporárias
            "querystring_expire": int(os.environ.get("AWS_S3_URL_EXPIRE", "3600")),
            "file_overwrite": False,
        },
    }

REST_FRAMEWORK: dict[str, Any] = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],  # negar por padrão
    "EXCEPTION_HANDLER": "config.errors.api_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_VERSION": "v1",
    "ALLOWED_VERSIONS": ["v1"],
    "DEFAULT_PAGINATION_CLASS": "config.pagination.StandardPagination",
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.AnonRateThrottle", "rest_framework.throttling.UserRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"anon": "100/hour", "user": "1000/hour", "login": "5/min"},
}


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,  # cada refresh devolve um refresh NOVO...
    "BLACKLIST_AFTER_ROTATION": True,  # ...e o antigo deixa de valer
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
CORS_ALLOWED_ORIGINS = [o for o in os.environ.get("CORS_ALLOWED_ORIGINS", "http://127.0.0.1:8200").split(",") if o]
CORS_URLS_REGEX = r"^/api/.*$"  # só a API fala com outras origens (o /admin/ não)
CORS_ALLOW_CREDENTIALS = False  # JWT vai no cabeçalho; sem cookies entre origens

CORS_ALLOW_HEADERS = (*default_headers, "idempotency-key")  # cabeçalho PERSONALIZADO do front precisa ser liberado no preflight
CORS_EXPOSE_HEADERS = ["Location", "Retry-After", "Idempotent-Replayed"]  # cabeçalhos que o JavaScript pode LER na resposta
CORS_PREFLIGHT_MAX_AGE = 600  # o navegador reaproveita o preflight por 10 min

# --- Celery e e-mail (aula 7.06) ---
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6390/0")
CELERY_RESULT_BACKEND = None  # não guardamos resultados: a tarefa tem efeito (e-mail), não valor
CELERY_TASK_IGNORE_RESULT = True
CELERY_TASK_SERIALIZER = "json"  # só dados simples: ids, textos (nunca objetos do ORM)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "UTC"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
EMAIL_BACKEND = "apps.orders.email_backend.SmtpLentoEmailBackend"
EMAIL_SIMULATED_DELAY = float(os.environ.get("EMAIL_SIMULATED_DELAY", "0.8"))  # segundos que o "SMTP" demora
EMAIL_OUTBOX_FILE = os.environ.get("EMAIL_OUTBOX_FILE", str(BASE_DIR / "outbox.jsonl"))
ORDER_EMAIL_MODE = os.environ.get("ORDER_EMAIL_MODE", "async")  # "sync" | "async" | "off"
DEFAULT_FROM_EMAIL = "MiniShop <nao-responda@minishop.local>"

# --- Agendamento (aula 7.08): quem LÊ isto é o `celery beat` ---
from celery.schedules import crontab  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    "limpar-chaves-de-idempotencia": {
        "task": "orders.limpar_chaves_de_idempotencia",
        "schedule": crontab(minute=0, hour=3),
    },  # todo dia, 03:00 UTC
    "cancelar-pedidos-pendentes": {
        "task": "orders.cancelar_pedidos_pendentes_antigos",
        "schedule": crontab(minute="*/15"),
    },  # a cada 15 min
    "reenviar-emails-falhos": {"task": "orders.reenviar_emails_falhos", "schedule": crontab(minute=5)},  # toda hora, no minuto 5
}
if os.environ.get("BEAT_DEMO") == "cron":  # demonstração: o mesmo "pulso", mas como crontab (todo minuto)
    CELERY_BEAT_SCHEDULE = {"pulso": {"task": "orders.batimento", "schedule": crontab(minute="*")}}
elif os.environ.get("BEAT_DEMO"):  # só para a demonstração da aula: um "pulso" a cada 2 s
    CELERY_BEAT_SCHEDULE = {"pulso": {"task": "orders.batimento", "schedule": 2.0}}

# --- Webhooks (aula 7.09) ---
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "whsec_lab_apenas_para_estudo")  # em produção: variável de ambiente, longa e aleatória

# --- WebSockets (aula 7.10): a camada de canais precisa ser COMPARTILHADA entre processos (Redis) ---
ASGI_APPLICATION = "config.asgi.application"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [(os.environ.get("REDIS_HOST", "127.0.0.1"), int(os.environ.get("REDIS_PORT", "6390")))]},
    }
}

# --- Gateway de pagamento (aula 8.04): o adaptador é escolhido por configuração ---
PAYMENT_GATEWAY = os.environ.get("PAYMENT_GATEWAY", "fake")  # "fake" | "acme"
ACME_BASE_URL = os.environ.get("ACME_BASE_URL", "http://127.0.0.1:8150")
ACME_WEBHOOK_SECRET = os.environ.get("ACME_WEBHOOK_SECRET", "acme_whsec_lab_apenas_para_estudo")


# Fator XI (logs são um fluxo de eventos): tudo em stdout, uma linha por evento; quem coleta é a plataforma.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"linha": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}},
    "handlers": {"stdout": {"class": "logging.StreamHandler", "stream": "ext://sys.stdout", "formatter": "linha"}},
    "root": {"handlers": ["stdout"], "level": os.environ.get("LOG_LEVEL", "INFO")},
}

# Segurança em produção (só quando DEBUG=False; atrás de proxy TLS).
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "3600"))

# --- Senhas (aula 9.04) ---
# O PRIMEIRO hasher grava as senhas novas; os demais só VERIFICAM as antigas. No login, o Django regrava o hash no primeiro da lista.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Superfície exposta (aula 9.06): em produção, só o necessário ---
EXPOSE_DOCS = env_bool("EXPOSE_DOCS", DEBUG)  # /api/docs, /api/redoc, /api/schema: documentação pública é decisão, não padrão
ENABLE_DEMO_ROUTES = DEBUG  # /demo/*: rotas de experimento da série; nunca em produção
ADMIN_URL = os.environ.get("ADMIN_URL", "admin/").strip("/") + "/"  # trocar o caminho não é segurança, mas reduz varredura automática
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
REST_FRAMEWORK["NUM_PROXIES"] = int(
    os.environ.get("NUM_PROXIES", "0")
)  # quantos proxies confiáveis estão na frente (IP real para o throttling)
ALLOW_SEED = DEBUG  # o comando `seed` cria usuários com senha conhecida: só em desenvolvimento

# --- Cache (aula 9.06) ---
# O contador do throttling vive no CACHE. O padrão (memória local) é POR PROCESSO: com N workers o limite real vira ~N vezes maior.
if os.environ.get("REDIS_CACHE_URL"):
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": os.environ["REDIS_CACHE_URL"]}}
