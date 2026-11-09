from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "lab-only-not-secret"
DEBUG = True
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions",
    "django.contrib.messages", "django.contrib.staticfiles",
    "corsheaders", "rest_framework", "drf_spectacular", "django_filters", "rest_framework_simplejwt", "rest_framework_simplejwt.token_blacklist",
    "apps.accounts", "apps.catalog", "apps.cart", "apps.orders",
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
