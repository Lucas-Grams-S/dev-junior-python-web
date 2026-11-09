"""Armadilhas clássicas dos mocks, documentadas como testes."""

from unittest.mock import Mock, create_autospec

import pytest

from apps.payments.gateway import Cobranca, PaymentGateway


# 1) Mock "solto" aceita QUALQUER coisa, inclusive método que não existe: o teste passa e o código está errado.
def test_mock_sem_spec_aceita_metodo_inexistente():
    gateway = Mock()
    gateway.criar_cobranca_com_erro_de_digitacao(10, 99)  # nenhum método assim existe na porta!
    gateway.criar_cobranca_com_erro_de_digitacao.assert_called_once_with(10, 99)  # ...e o teste fica verde


# 2) autospec copia a ASSINATURA da porta real: método inexistente e argumentos errados viram erro.
def test_autospec_recusa_metodo_inexistente():
    gateway = create_autospec(PaymentGateway, instance=True)
    with pytest.raises(AttributeError):
        gateway.criar_cobranca_com_erro_de_digitacao(10, 99)


def test_autospec_recusa_argumentos_errados():
    gateway = create_autospec(PaymentGateway, instance=True)
    with pytest.raises(TypeError):
        gateway.criar_cobranca(1, 2, 3, 4)  # a porta só tem (order_id, valor)
    gateway.criar_cobranca.return_value = Cobranca(ref="x")
    assert gateway.criar_cobranca(1, 10).ref == "x"


# 3) Patch no lugar ERRADO: troca o nome onde ele é DEFINIDO, mas o código usa o nome onde foi IMPORTADO.
@pytest.mark.xfail(strict=True, reason="armadilha didática: patch em apps.payments.gateway não afeta apps.payments.api")
def test_patch_no_alvo_errado_nao_tem_efeito(api_as, settings, criar_produto, cliente, monkeypatch):
    import apps.payments.api  # noqa: F401  (sem isto o resultado DEPENDE DA ORDEM: se a view ainda não foi importada, o patch "pega")
    from apps.cart import services as carrinho
    from apps.orders import services

    settings.ORDER_EMAIL_MODE = "off"
    carrinho.add_item(cliente, criar_produto(estoque=5).pk, 1)
    pedido = services.create_order(cliente)
    gateway = create_autospec(PaymentGateway, instance=True)
    gateway.criar_cobranca.return_value = Cobranca(ref="mock-1")
    monkeypatch.setattr("apps.payments.gateway.obter_gateway", lambda: gateway)  # ALVO ERRADO (onde é definido)
    api_as("cliente").post(f"/api/v1/orders/{pedido.pk}/pay/")
    gateway.criar_cobranca.assert_called_once()  # falha: quem respondeu foi o GatewayFake real
