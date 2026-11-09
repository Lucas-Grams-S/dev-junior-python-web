import os
import pathlib
import subprocess
import sys

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client

from apps.accounts.receivers import limpo

pytestmark = pytest.mark.django_db
RAIZ = pathlib.Path(__file__).resolve().parent.parent


# --- cabeçalhos ---------------------------------------------------------------------------------------------
def test_api_tem_csp_restritiva_e_demais_cabecalhos(client):
    r = client.get("/api/v1/categories/", secure=True)
    assert r["Content-Security-Policy"].startswith("default-src 'none'") and "frame-ancestors 'none'" in r["Content-Security-Policy"]
    assert "camera=()" in r["Permissions-Policy"]
    assert r["X-Content-Type-Options"] == "nosniff" and r["X-Frame-Options"] == "DENY"
    assert r["Referrer-Policy"] == "same-origin" and r["Cross-Origin-Opener-Policy"] == "same-origin"


def test_admin_e_docs_tem_csp_propria_sem_afrouxar_a_api(client):
    assert "default-src 'self'" in client.get("/admin/login/")["Content-Security-Policy"]
    assert "cdn.jsdelivr.net" in client.get("/api/docs/")["Content-Security-Policy"]  # DEBUG=1 nos testes → docs ligadas
    assert "cdn.jsdelivr.net" not in client.get("/api/v1/categories/")["Content-Security-Policy"]


# --- superfície exposta -------------------------------------------------------------------------------------
def rotas_em_producao(env_extra=None):
    env = {
        **os.environ,
        "DEBUG": "0",
        "SECRET_KEY": "x" * 60,
        "ALLOWED_HOSTS": "testserver",
        "DJANGO_SETTINGS_MODULE": "config.settings",
        **(env_extra or {}),
    }
    codigo = (
        "import django;django.setup();from django.test import Client;from django.urls import resolve, Resolver404\n"
        "c=Client()\n"
        "for u in ['/demo/sync/','/api/docs/','/api/schema/']:\n"
        "    print(u,'EXISTE' if c.get(u, secure=True).status_code!=404 else 'NAO_EXISTE')\n"
        "import django.conf as dc\n"
        "for u in ['/admin/login/','/painel-interno/login/']:\n"
        "    try: resolve(u); print(u,'EXISTE')\n"
        "    except Resolver404: print(u,'NAO_EXISTE')\n"
    )
    saida = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, env=env, cwd=RAIZ).stdout.split("\n")
    return dict(linha.split() for linha in saida if linha.split()[-1:] in (["EXISTE"], ["NAO_EXISTE"]) and len(linha.split()) == 2)


def test_em_producao_demo_e_docs_nao_existem_por_padrao():
    r = rotas_em_producao()
    assert r["/demo/sync/"] == "NAO_EXISTE" and r["/api/docs/"] == "NAO_EXISTE" and r["/api/schema/"] == "NAO_EXISTE"
    assert r["/admin/login/"] == "EXISTE"


def test_docs_podem_ser_ligadas_por_decisao_explicita():
    r = rotas_em_producao({"EXPOSE_DOCS": "1"})
    assert r["/api/docs/"] == "EXISTE" and r["/demo/sync/"] == "NAO_EXISTE"


def test_admin_pode_mudar_de_caminho():
    r = rotas_em_producao({"ADMIN_URL": "painel-interno"})
    assert r["/admin/login/"] == "NAO_EXISTE" and r["/painel-interno/login/"] == "EXISTE"


def test_seed_recusa_rodar_fora_do_desenvolvimento(settings):
    settings.ALLOW_SEED = False
    with pytest.raises(CommandError):
        call_command("seed")


# --- eventos de segurança (A09) ----------------------------------------------------------------------------
def test_login_falho_registra_quem_tentou_e_de_onde_sem_a_senha(caplog, seed):
    with caplog.at_level("WARNING", logger="security"):
        Client().post(
            "/api/v1/auth/token/",
            {"username": "cliente", "password": "senha-secreta-errada"},
            content_type="application/json",
            REMOTE_ADDR="203.0.113.7",
        )
    msgs = [r.getMessage() for r in caplog.records if r.name == "security"]
    assert any("login_failed username=cliente ip=203.0.113.7" in m for m in msgs)
    assert not any("senha-secreta-errada" in m for m in msgs)


def test_acesso_negado_e_registrado(caplog, seed):
    r = Client().post("/api/v1/auth/token/", {"username": "cliente", "password": "dev-somente-local-123"}, content_type="application/json")
    cli = Client(HTTP_AUTHORIZATION="Bearer " + r.json()["access"])
    with caplog.at_level("WARNING", logger="security"):
        assert cli.post("/api/v1/products/", {}, content_type="application/json").status_code == 403
    assert any("access_denied" in rec.getMessage() and "/api/v1/products/" in rec.getMessage() for rec in caplog.records)


def test_log_injection_e_neutralizado():
    assert limpo("maria\nlogin_ok username=admin") == "maria?login_ok username=admin"
    assert len(limpo("a" * 500)) == 64


# --- limitação de taxa: IP real atrás de proxy ---------------------------------------------------------------
def test_throttling_usa_o_ip_do_cliente_e_nao_o_do_proxy(settings):
    from rest_framework.request import Request
    from rest_framework.test import APIRequestFactory
    from rest_framework.throttling import AnonRateThrottle

    req = Request(APIRequestFactory().get("/", HTTP_X_FORWARDED_FOR="198.51.100.20, 203.0.113.9", REMOTE_ADDR="10.0.0.1"))
    from rest_framework.settings import api_settings

    api_settings.NUM_PROXIES = 1  # 1 proxy confiável na frente
    try:
        assert AnonRateThrottle().get_ident(req) == "203.0.113.9"  # o último IP adicionado pelo NOSSO proxy
        api_settings.NUM_PROXIES = 0  # sem proxy declarado: usa o endereço da conexão (não confia no cabeçalho)
        assert AnonRateThrottle().get_ident(req) == "10.0.0.1"
    finally:
        api_settings.NUM_PROXIES = 0


def test_cache_de_producao_precisa_ser_compartilhado_ou_o_limite_multiplica_por_worker(settings):
    # Regra operacional escrita como teste: se REDIS_CACHE_URL está definido, o backend NÃO pode ser a memória local.
    import importlib

    import config.settings as cfg

    os.environ["REDIS_CACHE_URL"] = "redis://127.0.0.1:6391/1"
    try:
        recarregado = importlib.reload(cfg)
        assert recarregado.CACHES["default"]["BACKEND"].endswith("RedisCache")
    finally:
        del os.environ["REDIS_CACHE_URL"]
        importlib.reload(cfg)
