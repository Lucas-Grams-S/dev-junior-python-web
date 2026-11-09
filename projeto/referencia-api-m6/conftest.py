import pytest
from django.core.management import call_command


@pytest.fixture
def seed(db):
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
