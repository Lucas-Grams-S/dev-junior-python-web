import pathlib

import pytest
import yaml
from django.core.management import call_command
from rest_framework.test import APIClient


def test_schema_gera_sem_avisos(tmp_path):
    destino = tmp_path / "schema.yml"
    call_command("spectacular", "--file", str(destino), "--validate", "--fail-on-warn")
    assert destino.stat().st_size > 0


@pytest.mark.django_db
def test_docs_estao_no_ar():
    c = APIClient()
    assert c.get("/api/schema/").status_code == 200 and c.get("/api/docs/").status_code == 200


@pytest.mark.django_db
def test_versao_nao_permitida_da_404():
    assert APIClient().get("/api/v2/categories/").status_code == 404


def test_schema_commitado_esta_em_dia(tmp_path):
    novo = tmp_path / "schema.yml"
    call_command("spectacular", "--file", str(novo), "--fail-on-warn")
    assert yaml.safe_load(novo.read_text()) == yaml.safe_load(pathlib.Path("schema.yml").read_text()), "schema mudou"
