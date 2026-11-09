from django.conf import settings
from django.db import models
from django.db.models import F, Q, Sum

from apps.catalog.models import Product


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrinho de {self.user_id}"

    def total(self):
        return self.items.aggregate(t=Sum(F("quantity") * F("product__price")))["t"] or 0

    def count(self):
        return self.items.aggregate(q=Sum("quantity"))["q"] or 0


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="+")
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["cart", "product"], name="cartitem_unique_product"),
            models.CheckConstraint(condition=Q(quantity__gt=0), name="cartitem_quantity_gt_0"),
        ]

    def __str__(self):
        return f"{self.quantity} × produto {self.product_id}"

    @property
    def subtotal(self):
        return self.quantity * self.product.price
