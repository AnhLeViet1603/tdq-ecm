from django.db import models
from shared.base_model import BaseModel


class Warehouse(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "warehouses"

    def __str__(self):
        return self.name


class Stock(BaseModel):
    product_id = models.UUIDField(db_index=True)  # FK to product service
    product_sku = models.CharField(max_length=100, blank=True)  # denormalized
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="stocks")
    quantity = models.PositiveIntegerField(default=0)
    reserved = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)

    class Meta:
        db_table = "stocks"
        unique_together = ("product_id", "warehouse")

    @property
    def available(self):
        return max(0, self.quantity - self.reserved)

    def __str__(self):
        return f"{self.product_sku} @ {self.warehouse.name}: {self.available} available"


class StockHistory(BaseModel):
    REASON_CHOICES = [
        ("purchase", "Purchase / Restock"),
        ("sale", "Sale"),
        ("adjustment", "Manual Adjustment"),
        ("return", "Customer Return"),
        ("damage", "Damaged / Write-off"),
        ("transfer", "Warehouse Transfer"),
    ]
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name="history")
    quantity_change = models.IntegerField()   # positive = in, negative = out
    quantity_before = models.IntegerField()
    quantity_after = models.IntegerField()
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    reference_id = models.UUIDField(null=True, blank=True)  # order_id, purchase_id, etc.
    note = models.TextField(blank=True)
    performed_by = models.UUIDField(null=True, blank=True)  # user_id

    class Meta:
        db_table = "stock_history"
        ordering = ["-created_at"]
