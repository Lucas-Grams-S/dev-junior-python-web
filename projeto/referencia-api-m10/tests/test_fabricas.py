"""As fábricas de teste também são código: um teste curto garante que os padrões continuam sensatos."""

import pytest

pytestmark = pytest.mark.django_db


def test_produto_padrao_e_valido_e_ativo(criar_produto):
    p = criar_produto()
    assert p.is_active and p.stock == 5 and str(p.price) == "10.00" and p.sku.startswith("TST-")


def test_so_o_que_importa_e_dito_no_teste(criar_produto):
    p = criar_produto(estoque=0, ativo=False)
    assert (p.stock, p.is_active) == (0, False)


def test_skus_automaticos_nao_colidem(criar_produto):
    assert len({criar_produto().sku for _ in range(5)}) == 5


def test_usuario_criado_pode_autenticar(criar_usuario):
    u = criar_usuario()
    assert u.check_password("dev-somente-local-123")
