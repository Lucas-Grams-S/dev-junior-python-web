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


LIMITES_DO_BANCO = {2147483647, 9223372036854775807}  # maior inteiro de 32/64 bits: vem do BANCO, não da API


def _sem_limites_do_banco(no):
    """O drf-spectacular deriva `maximum`/`format: int64` de campos inteiros positivos do banco (SQLite: 64 bits; PostgreSQL: 32).
    Isso é acidente de ambiente, não contrato: removemos só esses valores antes de comparar."""
    if isinstance(no, dict):
        return {
            k: _sem_limites_do_banco(v)
            for k, v in no.items()
            if not (k == "maximum" and v in LIMITES_DO_BANCO) and not (k == "format" and v == "int64")
        }
    if isinstance(no, list):
        return [_sem_limites_do_banco(v) for v in no]
    return no


def test_schema_commitado_esta_em_dia(tmp_path):
    novo = tmp_path / "schema.yml"
    call_command("spectacular", "--file", str(novo), "--fail-on-warn")
    atual = _sem_limites_do_banco(yaml.safe_load(novo.read_text()))
    assert atual == _sem_limites_do_banco(yaml.safe_load(pathlib.Path("schema.yml").read_text())), "schema mudou"
