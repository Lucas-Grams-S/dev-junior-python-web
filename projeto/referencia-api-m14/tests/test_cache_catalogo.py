"""Cache do catálogo (módulo 14, aula 03): HIT/MISS, invalidação (inclusive por ESTOQUE), falha aberta e segurança."""

import time

import pytest
from django.core.cache import cache

from apps.catalog.models import Product

pytestmark = pytest.mark.django_db


def primeiro_produto():
    return Product.objects.filter(is_active=True).order_by("pk").first()


def test_anonimo_miss_depois_hit_sem_tocar_o_banco(api_as, django_assert_num_queries):
    anon = api_as(None)
    assert anon.get("/api/v1/products/")["X-Cache"] == "MISS"
    with django_assert_num_queries(0):  # a resposta veio do cache: zero consultas
        r = anon.get("/api/v1/products/")
    assert r["X-Cache"] == "HIT" and r.json()["count"] > 0


def test_hit_devolve_exatamente_o_mesmo_corpo(api_as):
    anon = api_as(None)
    a = anon.get("/api/v1/products/", {"ordering": "-price", "page": 2})
    b = anon.get("/api/v1/products/", {"ordering": "-price", "page": 2})
    assert (a["X-Cache"], b["X-Cache"]) == ("MISS", "HIT") and a.json() == b.json()


def test_consultas_diferentes_tem_chaves_diferentes(api_as):
    anon = api_as(None)
    anon.get("/api/v1/products/", {"search": "mouse"})
    assert anon.get("/api/v1/products/", {"search": "cadeira"})["X-Cache"] == "MISS"
    assert anon.get("/api/v1/products/", {"search": "mouse"})["X-Cache"] == "HIT"


def test_detalhe_tambem_usa_cache(api_as):
    p = primeiro_produto()
    anon = api_as(None)
    assert anon.get(f"/api/v1/products/{p.pk}/")["X-Cache"] == "MISS"
    assert anon.get(f"/api/v1/products/{p.pk}/")["X-Cache"] == "HIT"


def test_logado_nao_usa_nem_alimenta_o_cache(api_as):
    r = api_as("cliente").get("/api/v1/products/")
    assert r["X-Cache"] == "BYPASS"
    assert api_as(None).get("/api/v1/products/")["X-Cache"] == "MISS"  # o logado não encheu o cache


def test_equipe_ve_inativos_e_isso_nao_vaza_para_anonimos(api_as):
    p = primeiro_produto()
    Product.objects.filter(pk=p.pk).update(is_active=False)
    cache.clear()
    staff = api_as("gerente").get("/api/v1/products/", {"search": p.name})
    assert any(x["id"] == p.pk for x in staff.json()["results"])
    anon = api_as(None).get("/api/v1/products/", {"search": p.name})
    assert all(x["id"] != p.pk for x in anon.json()["results"])


def test_alterar_produto_invalida_o_catalogo(api_as, django_capture_on_commit_callbacks):
    p = primeiro_produto()
    anon = api_as(None)
    assert anon.get(f"/api/v1/products/{p.pk}/").json()["name"] == p.name
    with django_capture_on_commit_callbacks(execute=True):
        p.name = "Nome Novo Do Produto"
        p.save()
    r = anon.get(f"/api/v1/products/{p.pk}/")
    assert r["X-Cache"] == "MISS" and r.json()["name"] == "Nome Novo Do Produto"


def test_pedido_e_cancelamento_invalidam_por_causa_do_estoque(api_as, django_capture_on_commit_callbacks, settings):
    """O estoque muda por `.update(F(...))`, que NÃO dispara signals: sem o bump explícito, o catálogo mostraria estoque velho."""
    settings.ORDER_EMAIL_MODE = "off"  # sem fila neste teste
    p = primeiro_produto()
    anon, cli = api_as(None), api_as("cliente")
    antes = anon.get(f"/api/v1/products/{p.pk}/").json()["stock"]
    cli.post("/api/v1/cart/items/", {"product": p.pk, "quantity": 2}, format="json")
    with django_capture_on_commit_callbacks(execute=True):
        pedido = cli.post("/api/v1/orders/").json()
    r = anon.get(f"/api/v1/products/{p.pk}/")
    assert r["X-Cache"] == "MISS" and r.json()["stock"] == antes - 2
    with django_capture_on_commit_callbacks(execute=True):
        assert cli.post(f"/api/v1/orders/{pedido['id']}/cancel/").status_code == 200
    assert anon.get(f"/api/v1/products/{p.pk}/").json()["stock"] == antes


def test_sem_invalidar_o_estoque_fica_velho_ate_o_ttl(api_as):
    """A PROVA do porquê do bump: mudando o estoque 'por fora' do caminho invalidado, o cache mente."""
    p = primeiro_produto()
    anon = api_as(None)
    antes = anon.get(f"/api/v1/products/{p.pk}/").json()["stock"]
    Product.objects.filter(pk=p.pk).update(stock=antes + 100)  # sem signal, sem bump
    assert anon.get(f"/api/v1/products/{p.pk}/").json()["stock"] == antes  # velho, de propósito


def test_ttl_expira(api_as, settings):
    settings.CATALOG_CACHE_TTL = 1
    anon = api_as(None)
    anon.get("/api/v1/products/")
    assert anon.get("/api/v1/products/")["X-Cache"] == "HIT"
    time.sleep(1.2)
    assert anon.get("/api/v1/products/")["X-Cache"] == "MISS"


class CacheQuebrado:
    def __getattr__(self, nome):
        def falha(*a, **k):
            raise ConnectionError("redis fora do ar")

        return falha


def test_cache_fora_do_ar_nao_derruba_o_catalogo(api_as, monkeypatch):
    monkeypatch.setattr("apps.catalog.cache.cache", CacheQuebrado())  # só o cache DO CATÁLOGO quebra
    r = api_as(None).get("/api/v1/products/")
    assert r.status_code == 200 and r["X-Cache"] == "MISS" and r.json()["count"] > 0


def test_limite_de_taxa_tambem_falha_aberto_quando_o_cache_cai(api_as, monkeypatch):
    """Sem isto, a queda do Redis transformaria TODA requisição em 500 (o contador do throttling vive no cache)."""
    anon, cli = api_as(None), api_as("cliente")  # o login (estrito) acontece ANTES de o cache "cair"
    monkeypatch.setattr("rest_framework.throttling.SimpleRateThrottle.cache", CacheQuebrado())
    monkeypatch.setattr("apps.catalog.cache.cache", CacheQuebrado())
    assert anon.get("/api/v1/products/").status_code == 200
    assert cli.get("/api/v1/products/").status_code == 200


def test_login_continua_estrito_sem_cache(monkeypatch):
    """Escolha deliberada: o limite de LOGIN não falha aberto (brute force). Sem cache, o login falha em vez de ficar sem proteção."""
    monkeypatch.setattr("rest_framework.throttling.SimpleRateThrottle.cache", CacheQuebrado())
    from django.test import Client

    r = Client(raise_request_exception=False).post(
        "/api/v1/auth/token/", {"username": "x", "password": "y"}, content_type="application/json"
    )
    assert r.status_code == 503 and r.json()["code"] == "service_unavailable"
