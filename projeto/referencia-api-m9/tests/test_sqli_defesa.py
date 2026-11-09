import pytest

from apps.catalog.models import Category, Product
from seclab.consultas import buscar_segura, buscar_segura_sql_cru

pytestmark = pytest.mark.django_db


@pytest.fixture
def produtos():
    cat = Category.objects.create(name="Geral", slug="geral")
    for sku, nome, ativo in [("A-1", "Caneta azul", True), ("A-2", "Caderno O'Brien", True), ("A-3", "Cola 100% branca", True), ("A-4", "Item oculto", False)]:
        Product.objects.create(category=cat, sku=sku, name=nome, price="10.00", stock=1, is_active=ativo)


@pytest.mark.parametrize("buscar", [buscar_segura, buscar_segura_sql_cru])
class TestBuscaSegura:
    def test_apostrofo_e_texto_comum(self, produtos, buscar):
        assert [s for s, _ in buscar("O'Brien")] == ["A-2"]

    def test_entrada_com_aspas_e_comentario_nao_muda_a_consulta(self, produtos, buscar):
        assert buscar("x' OR '1'='1") == []                  # é só um texto que ninguém tem no nome
        assert buscar("'; --") == []

    def test_nunca_devolve_inativos(self, produtos, buscar):
        assert buscar("oculto") == []

    def test_busca_normal_continua_funcionando(self, produtos, buscar):
        assert [s for s, _ in buscar("caneta")] == ["A-1"]


def test_curinga_percent_e_literal_na_versao_com_escape(produtos):
    assert [s for s, _ in buscar_segura_sql_cru("100%")] == ["A-3"]
    assert buscar_segura_sql_cru("%") == [("A-3", "Cola 100% branca")]     # só quem tem '%' no nome
