from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.orders.models import Order


class PedidoConsumer(AsyncJsonWebsocketConsumer):
    """ws://.../ws/pedidos/<id>/?token=<access>: o cliente acompanha o status do SEU pedido em tempo real."""

    async def connect(self):
        user = self.scope["user"]
        if user is None:
            return await self.close(code=4401)  # não autenticado: recusa o handshake (o cliente vê HTTP 403)
        self.pedido_id = int(self.scope["url_route"]["kwargs"]["pedido_id"])
        status = await self._status_do_pedido(user.pk)
        if status is None:
            return await self.close(
                code=4403
            )  # pedido inexistente OU de outra pessoa (AUTORIZAÇÃO também no WebSocket): handshake recusado
        self.grupo = f"pedido_{self.pedido_id}"
        await self.channel_layer.group_add(self.grupo, self.channel_name)
        await self.accept()
        await self.send_json({"tipo": "estado_atual", "status": status})

    async def disconnect(self, code):
        if hasattr(self, "grupo"):
            await self.channel_layer.group_discard(self.grupo, self.channel_name)

    async def pedido_atualizado(self, evento):  # mensagens do grupo (type="pedido.atualizado")
        await self.send_json({"tipo": "atualizacao", "status": evento["status"]})

    @database_sync_to_async
    def _status_do_pedido(self, user_id):
        return Order.objects.filter(pk=self.pedido_id, user_id=user_id).values_list("status", flat=True).first()
