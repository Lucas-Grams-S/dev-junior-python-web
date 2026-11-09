"""Eventos internos do app de pagamentos. Quem quiser REAGIR (WebSocket, métricas...) se conecta aqui; o serviço não conhece ninguém."""
from django.dispatch import Signal

pedido_pago = Signal()          # kwargs: order_id, status
