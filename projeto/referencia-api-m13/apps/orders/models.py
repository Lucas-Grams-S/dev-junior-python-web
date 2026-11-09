from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.catalog.models import Product


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        PAID = "paid", "Pago"
        CANCELLED = "cancelled", "Cancelado"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [models.CheckConstraint(condition=Q(total__gte=0), name="order_total_gte_0")]

    def __str__(self):
        return f"Pedido #{self.pk} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="+")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name="orderitem_quantity_gt_0"),
            models.UniqueConstraint(fields=["order", "product"], name="orderitem_unique_product"),
        ]

    def __str__(self):
        return f"{self.quantity} × produto {self.product_id}"

    @property
    def subtotal(self):
        return self.quantity * self.unit_price


class IdempotencyKey(models.Model):
    """Guarda a resposta de um POST já processado, para que repetir a MESMA chave devolva o MESMO resultado."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    key = models.CharField(max_length=64)
    response_status = models.PositiveSmallIntegerField()
    response_body = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "key"], name="idempotency_user_key_unique")]

    def __str__(self):
        return f"{self.key} (usuário {self.user_id})"


class EmailLog(models.Model):
    """Registro de cada e-mail por (pedido, tipo): é o que torna a tarefa IDEMPOTENTE."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        SENDING = "sending", "Enviando"
        SENT = "sent", "Enviado"
        FAILED = "failed", "Falhou"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="emails")
    kind = models.CharField(max_length=40)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    attempts = models.PositiveIntegerField(default=0)
    claimed_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=200, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["order", "kind"], name="emaillog_order_kind_unique")]

    def __str__(self):
        return f"{self.kind} do pedido {self.order_id}: {self.status}"
