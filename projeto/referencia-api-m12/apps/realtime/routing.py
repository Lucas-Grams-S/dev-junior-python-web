from django.urls import path

from .consumers import PedidoConsumer

# django-stubs espera uma view HTTP em `path()`; o Channels usa o mesmo `path()` para consumers ASGI (incompatibilidade só de tipos)
websocket_urlpatterns = [path("ws/pedidos/<int:pedido_id>/", PedidoConsumer.as_asgi())]  # type: ignore[arg-type]
