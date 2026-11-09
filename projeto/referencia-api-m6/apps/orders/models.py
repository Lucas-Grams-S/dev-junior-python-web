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
