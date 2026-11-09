from django.db import models
from django.db.models import Q

from apps.orders.models import Order


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        PAID = "paid", "Pago"
        FAILED = "failed", "Falhou"
        REFUNDED = "refunded", "Estornado"

    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name="payment")
    provider_ref = models.CharField(max_length=64, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(amount__gte=0), name="payment_amount_gte_0")]

    def __str__(self):
        return f"Pagamento {self.provider_ref} ({self.status})"


class WebhookEvent(models.Model):
    """Cada evento recebido do gateway, UMA vez (event_id único): é o que torna o webhook idempotente e auditável."""

    class Result(models.TextChoices):
        PROCESSED = "processed", "Processado"
        IGNORED = "ignored", "Ignorado (fora de ordem ou irrelevante)"
        REJECTED = "rejected", "Rejeitado (inconsistente)"

    event_id = models.CharField(max_length=64, unique=True)
    type = models.CharField(max_length=40)
    payload = models.JSONField()
    result = models.CharField(max_length=10, choices=Result.choices)
    detail = models.CharField(max_length=200, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_id}: {self.result}"


class OutboxEvent(models.Model):
    """Padrão 'outbox transacional': o evento é gravado NA MESMA transação que muda o estado; um relé publica depois."""

    type = models.CharField(max_length=60)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["published_at", "id"], name="outbox_pendentes_idx")]

    def __str__(self):
        return f"{self.type} #{self.pk}"


class MensagemProcessada(models.Model):
    """Do lado do CONSUMIDOR: cada message_id é processado uma única vez (consumidor idempotente)."""

    message_id = models.CharField(max_length=64, unique=True)
    processed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message_id
