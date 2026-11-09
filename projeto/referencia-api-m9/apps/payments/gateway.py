"""PORTA (interface) para gateways de pagamento + ADAPTADORES por provedor + FÁBRICA que escolhe o adaptador pela configuração.

O resto do sistema só conhece `Cobranca` e `EventoPagamento` (o vocabulário DO MINISHOP); cada adaptador traduz de/para o vocabulário do provedor."""
import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Protocol

import httpx
from django.conf import settings

from .security import AssinaturaInvalida, verificar


@dataclass(frozen=True)
class Cobranca:
    ref: str                    # identificador da cobrança no provedor
    status: str = "pending"


@dataclass(frozen=True)
class EventoPagamento:
    id: str                     # id ÚNICO do evento (idempotência)
    tipo: str                   # vocabulário do MiniShop: "paid" | "failed" | "refunded" | "ignored"
    payment_ref: str
    valor: Decimal | None = None
    bruto: dict = field(default_factory=dict)


class GatewayIndisponivel(Exception):
    """O provedor não respondeu / respondeu com erro (transitório)."""


class PaymentGateway(Protocol):
    def criar_cobranca(self, order_id: int, valor: Decimal) -> Cobranca: ...
    def interpretar_webhook(self, cabecalhos, corpo: bytes) -> EventoPagamento: ...


# ----------------------------------------------------------------------------------------------- adaptador 1: o "fake" local
class GatewayFake:
    """Usado em desenvolvimento e nos testes: gera a referência localmente e fala o 'dialeto' da aula 7.09."""

    TIPOS = {"payment.succeeded": "paid", "payment.failed": "failed", "payment.refunded": "refunded"}

    def criar_cobranca(self, order_id, valor):
        return Cobranca(ref="pay_" + uuid.uuid4().hex[:16])

    def interpretar_webhook(self, cabecalhos, corpo):
        verificar(settings.WEBHOOK_SECRET, corpo, cabecalhos.get("X-Signature"))           # levanta AssinaturaInvalida
        bruto = json.loads(corpo)
        dados = bruto.get("data", {})
        valor = Decimal(str(dados["amount"])) if "amount" in dados else None
        return EventoPagamento(bruto["id"], self.TIPOS.get(bruto["type"], "ignored"), dados.get("payment_ref", ""), valor, bruto)


# ----------------------------------------------------------------------------------------------- adaptador 2: um provedor HTTP "Acme Pay"
class GatewayAcme:
    """Fala com o 'Acme Pay': outro formato de requisição (centavos), outros nomes de estado e OUTRA assinatura de webhook."""

    EVENTOS = {"charge.captured": "paid", "charge.declined": "failed", "charge.refunded": "refunded"}
    TOLERANCIA = 300

    def __init__(self, base_url, segredo_webhook, client=None):
        self.client = client or httpx.Client(base_url=base_url, timeout=httpx.Timeout(5, read=3))
        self.segredo = segredo_webhook

    def criar_cobranca(self, order_id, valor):
        corpo = {"amount_cents": int(valor * 100), "currency": "BRL", "reference": f"order-{order_id}"}
        chave = f"order-{order_id}"                                                         # idempotência: repetir NÃO cobra duas vezes
        for tentativa in range(3):
            try:
                r = self.client.post("/v1/charges", json=corpo, headers={"Idempotency-Key": chave})
            except (httpx.ConnectError, httpx.TimeoutException):
                r = None
            if r is not None and r.status_code in (200, 201):
                return Cobranca(ref=r.json()["charge_id"], status="pending")
            if r is not None and r.status_code < 500:
                raise GatewayIndisponivel(f"Acme recusou a cobrança: HTTP {r.status_code}")        # erro do pedido: não adianta repetir
            time.sleep(0.05 * 2 ** tentativa)
        raise GatewayIndisponivel("Acme indisponível após 3 tentativas")

    def interpretar_webhook(self, cabecalhos, corpo):
        recebida = cabecalhos.get("X-Acme-Signature", "")
        esperada = "sha256=" + hmac.new(self.segredo.encode(), corpo, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(esperada, recebida):
            raise AssinaturaInvalida("assinatura da Acme não confere")
        bruto = json.loads(corpo)
        if abs(time.time() - bruto["created"]) > self.TOLERANCIA:
            raise AssinaturaInvalida("evento antigo demais (replay?)")
        cobranca = bruto["charge"]
        return EventoPagamento(bruto["id"], self.EVENTOS.get(bruto["event"], "ignored"), cobranca["id"],
                               Decimal(cobranca["amount_cents"]) / 100, bruto)               # centavos → Decimal


# ----------------------------------------------------------------------------------------------- fábrica
def obter_gateway() -> PaymentGateway:
    """Escolhe o adaptador pela configuração (PAYMENT_GATEWAY): trocar de provedor é UMA variável de ambiente."""
    nome = getattr(settings, "PAYMENT_GATEWAY", "fake")
    if nome == "fake":
        return GatewayFake()
    if nome == "acme":
        return GatewayAcme(settings.ACME_BASE_URL, settings.ACME_WEBHOOK_SECRET)
    raise ValueError(f"PAYMENT_GATEWAY desconhecido: {nome!r}")
