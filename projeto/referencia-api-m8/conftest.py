import pytest
from django.core.management import call_command


def _zera_sequences():
    """Os testes assumem ids previsíveis (produto 1, 2…). No SQLite o rollback reinicia o contador; no PostgreSQL as
    sequences NÃO são revertidas pela transação. Zeramos (as sequences voltam ao maior id existente) para os dois bancos se comportarem igual."""
    from django.apps import apps
    from django.core.management.color import no_style
    from django.db import connection
    if connection.vendor != "postgresql":
        return
    modelos = [m for m in apps.get_models() if m._meta.managed and m._meta.pk.get_internal_type() in ("AutoField", "BigAutoField")]
    # `sequence_reset_sql` calcula a partir do MAIOR id existente (seguro para tabelas com dados de migração, como grupos e permissões).
    # `sequence_reset_by_name_sql` zera tudo para 1: serve DEPOIS de um TRUNCATE, e quebraria inserções em tabelas que já têm linhas.
    sql = connection.ops.sequence_reset_sql(no_style(), modelos)
    with connection.cursor() as c:
        for stmt in sql:
            c.execute(stmt)


@pytest.fixture
def seed(db):
    _zera_sequences()
    call_command("seed")


@pytest.fixture
def cliente(seed, django_user_model):
    return django_user_model.objects.get(username="cliente")


@pytest.fixture
def gerente(seed, django_user_model):
    return django_user_model.objects.get(username="gerente")


@pytest.fixture
def api_anonimo():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture(autouse=True)
def _limpa_cache():
    from django.core.cache import cache
    cache.clear()          # o contador do throttling vive no cache: zera entre os testes
    yield


@pytest.fixture
def api_as(seed):
    """Fábrica: api_as("gerente") devolve um APIClient autenticado por JWT REAL (login de verdade); api_as(None) é anônimo."""
    from rest_framework.test import APIClient

    def _fabrica(username=None, senha="dev-somente-local-123"):
        c = APIClient()
        if username:
            r = c.post("/api/v1/auth/token/", {"username": username, "password": senha}, format="json")
            assert r.status_code == 200, r.content
            c.credentials(HTTP_AUTHORIZATION="Bearer " + r.json()["access"])
        return c
    return _fabrica
