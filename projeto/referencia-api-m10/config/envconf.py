"""Leitura de configuração do ambiente (Fator III), sem dependências externas."""

import os
from urllib.parse import unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

_VERDADE = {"1", "true", "yes", "on"}


def env_bool(nome: str, padrao: bool = False) -> bool:
    valor = os.environ.get(nome)
    return padrao if valor is None else valor.strip().lower() in _VERDADE


def env_list(nome: str, padrao: list[str]) -> list[str]:
    valor = os.environ.get(nome)
    return padrao if valor is None else [v.strip() for v in valor.split(",") if v.strip()]


def database_from_url(url: str) -> dict:
    """sqlite:///caminho  |  postgres://usuario:senha@host:porta/banco"""
    u = urlparse(url)
    if u.scheme == "sqlite":
        return {"ENGINE": "django.db.backends.sqlite3", "NAME": unquote(u.path[1:])}
    if u.scheme in ("postgres", "postgresql"):
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": u.path.lstrip("/"),
            "USER": unquote(u.username or ""),
            "PASSWORD": unquote(u.password or ""),
            "HOST": u.hostname or "",
            "PORT": str(u.port or ""),
            "CONN_MAX_AGE": 60,
        }
    raise ImproperlyConfigured(f"DATABASE_URL com esquema não suportado: {u.scheme!r}")
