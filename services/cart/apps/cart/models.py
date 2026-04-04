from django.db import models
from shared.base_model import BaseModel


class Cart(BaseModel):
    user_id = models.UUIDField(unique=True, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "carts"

    def __str__(self):
        return f"Cart({self.user_id})"

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())


class CartItem(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product_id = models.UUIDField(db_index=True)
    product_sku = models.CharField(max_length=100, blank=True)     # denormalized
    product_name = models.CharField(max_length=500)                 # denormalized
    product_image = models.URLField(blank=True)                     # denormalized
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    attributes = models.JSONField(default=dict)  # {"color": "red", "size": "XL"}

    class Meta:
        db_table = "cart_items"
        unique_together = ("cart", "product_id")

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"
