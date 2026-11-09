import pytest
from channels.layers import get_channel_layer
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from rest_framework_simplejwt.tokens import AccessToken

from apps.cart import services as carrinho
from apps.catalog.models import Product
from apps.orders import services
from apps.realtime.auth import JWTQueryMiddleware
from apps.realtime.routing import websocket_urlpatterns

app = JWTQueryMiddleware(URLRouter(websocket_urlpatterns))


@pytest.fixture(autouse=True)
def camada_em_memoria(settings):
    settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}   # sem Redis nos testes


@pytest.fixture
def pedido(cliente, db):
    carrinho.add_item(cliente, Product.objects.get(sku="INF-002").pk, 1)      # por SKU: os ids mudam depois de um flush
    return services.create_order(cliente)


def url(pedido, user=None):
    t = f"?token={AccessToken.for_user(user)}" if user else ""
    return f"/ws/pedidos/{pedido.pk}/{t}"


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
async def test_sem_token_e_recusado(pedido):
    com = WebsocketCommunicator(app, url(pedido))
    conectou, _ = await com.connect()
    assert conectou is False


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
async def test_outro_usuario_nao_acompanha_o_pedido(pedido, gerente):
    com = WebsocketCommunicator(app, url(pedido, gerente))
    conectou, _ = await com.connect()
    assert conectou is False


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
async def test_dono_recebe_estado_inicial_e_atualizacao(pedido, cliente):
    com = WebsocketCommunicator(app, url(pedido, cliente))
    conectou, _ = await com.connect()
    assert conectou
    assert await com.receive_json_from() == {"tipo": "estado_atual", "status": "pending"}
    await get_channel_layer().group_send(f"pedido_{pedido.pk}", {"type": "pedido.atualizado", "status": "paid"})
    assert await com.receive_json_from() == {"tipo": "atualizacao", "status": "paid"}
    await com.disconnect()
