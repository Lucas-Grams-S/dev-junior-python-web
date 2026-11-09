import pytest
from django.core.management import call_command


def _zera_sequences():
    """Os testes assumem ids previsíveis (produto 1, 2…). No SQLite o rollback reinicia o contador; no PostgreSQL as
    sequences NÃO são revertidas pela transação. Ajustamos as sequences (voltam ao maior id existente)
    para os dois bancos se comportarem igual."""
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

    cache.clear()  # o contador do throttling vive no cache: zera entre os testes
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


@pytest.fixture
def hasher_de_producao(settings):
    """Para os poucos testes que verificam o COMPORTAMENTO do hash real (Argon2id, migração de hashes)."""
    from config import settings as producao

    settings.PASSWORD_HASHERS = producao.PASSWORD_HASHERS


# --- Pirâmide de testes: cada teste ganha um marcador de nível, pelo que ele USA (aula 10.01) ---------------------
import inspect  # noqa: E402

FIXTURES_DE_API = {"client", "api_as", "api_anonimo", "admin_client", "admin_user"}
USOS_DE_API = ("Client(", "APIClient(", "client.", "cliente_http(")
FIXTURES_DE_BANCO = {"db", "transactional_db", "seed", "django_db_reset_sequences"}


def pytest_collection_modifyitems(items):
    for item in items:
        fixtures = set(getattr(item, "fixturenames", []))
        try:
            codigo = inspect.getsource(item.function)
        except (OSError, TypeError):
            codigo = ""
        usa_banco = bool(fixtures & FIXTURES_DE_BANCO) or item.get_closest_marker("django_db") is not None
        usa_api = bool(fixtures & FIXTURES_DE_API) or any(u in codigo for u in USOS_DE_API)
        if usa_api:
            item.add_marker("api")
        elif usa_banco:
            item.add_marker("integracao")
        else:
            item.add_marker("unidade")


# --- Fábricas como fixtures: o teste diz só o que IMPORTA; o resto vem com padrões sensatos (aula 10.01) ---------
import itertools  # noqa: E402
from decimal import Decimal  # noqa: E402


@pytest.fixture
def criar_produto(db):
    contador = itertools.count(1)

    def _criar(sku=None, nome=None, preco="10.00", estoque=5, ativo=True, categoria=None, **extra):
        from apps.catalog.models import Category, Product

        categoria = categoria or Category.objects.get_or_create(slug="geral", defaults={"name": "Geral"})[0]
        n = next(contador)
        return Product.objects.create(
            category=categoria,
            sku=sku or f"TST-{n:03d}",
            name=nome or sku or f"Produto {n}",
            price=Decimal(preco),
            stock=estoque,
            is_active=ativo,
            **extra,
        )

    return _criar


@pytest.fixture
def criar_usuario(db, django_user_model):
    contador = itertools.count(1)

    def _criar(username=None, senha="dev-somente-local-123", **extra):
        n = next(contador)
        return django_user_model.objects.create_user(username=username or f"usuario{n}", password=senha, **extra)

    return _criar
