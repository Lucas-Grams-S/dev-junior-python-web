from django.urls import path

from .consumers import PedidoConsumer

websocket_urlpatterns = [path("ws/pedidos/<int:pedido_id>/", PedidoConsumer.as_asgi())]
