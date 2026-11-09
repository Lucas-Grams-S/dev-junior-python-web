import pytest
from django.test import Client

from config.asgi import application as asgi_app
from config.wsgi import application as wsgi_app


def test_pontos_de_entrada_importaveis():
    assert callable(wsgi_app) and callable(asgi_app)


@pytest.mark.django_db
def test_api_responde_no_django():
    assert Client().get("/api/v1/categories/").status_code == 200
