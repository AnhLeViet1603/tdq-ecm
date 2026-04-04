from django.db import models
from shared.base_model import BaseModel


class Order(BaseModel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    ]
    user_id = models.UUIDField(db_index=True)
    order_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)

    # Pricing
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    # References
    coupon_code = models.CharField(max_length=50, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    shipping_method = models.CharField(max_length=100, blank=True)

    # Address (denormalized JSON snapshot)
    shipping_address = models.JSONField()
    billing_address = models.JSONField(null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]

    def __str__(self):
        return self.order_number


class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_id = models.UUIDField()
    product_sku = models.CharField(max_length=100, blank=True)
    product_name = models.CharField(max_length=500)
    product_image = models.URLField(blank=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    attributes = models.JSONField(default=dict)

    class Meta:
        db_table = "order_items"

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"


class OrderHistory(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="history")
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.UUIDField(null=True, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        db_table = "order_history"
        ordering = ["-created_at"]
