import pytest
from django.core.exceptions import ImproperlyConfigured

from config.envconf import database_from_url, env_bool, env_list


def test_sqlite_relativo_e_absoluto():
    assert database_from_url("sqlite:///rel.db")["NAME"] == "rel.db"
    assert database_from_url("sqlite:////tmp/abs.db")["NAME"] == "/tmp/abs.db"


def test_postgres_decodifica_senha_com_caracteres_especiais():
    cfg = database_from_url("postgres://app:p%40ss%2Fw@db.exemplo:5433/minishop")
    assert (cfg["USER"], cfg["PASSWORD"], cfg["HOST"], cfg["PORT"], cfg["NAME"]) == ("app", "p@ss/w", "db.exemplo", "5433", "minishop")
    assert cfg["ENGINE"].endswith("postgresql")


def test_esquema_desconhecido_falha_cedo():
    with pytest.raises(ImproperlyConfigured):
        database_from_url("mysql://x/y")


@pytest.mark.parametrize("valor,esperado", [("1", True), ("TRUE", True), ("off", False), ("", False), ("talvez", False)])
def test_env_bool(monkeypatch, valor, esperado):
    monkeypatch.setenv("X", valor)
    assert env_bool("X") is esperado


def test_env_list(monkeypatch):
    monkeypatch.setenv("H", " a.com, b.com ,,")
    assert env_list("H", []) == ["a.com", "b.com"]
    monkeypatch.delenv("H")
    assert env_list("H", ["z"]) == ["z"]


def test_postgres_aceita_sslmode_na_url():
    cfg = database_from_url("postgres://u:p@banco.exemplo:5432/d?sslmode=require&connect_timeout=5")
    assert cfg["OPTIONS"] == {"sslmode": "require", "connect_timeout": "5"}


def test_postgres_sem_query_tem_options_vazio():
    assert database_from_url("postgres://u:p@h:5432/d")["OPTIONS"] == {}


def test_postgres_rejeita_parametro_desconhecido():
    # um erro de digitação (ssl_mode) NÃO pode virar "sem TLS" em silêncio
    with pytest.raises(ImproperlyConfigured, match="ssl_mode"):
        database_from_url("postgres://u:p@h:5432/d?ssl_mode=require")
