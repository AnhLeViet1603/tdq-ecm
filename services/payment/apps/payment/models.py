from django.db import models
from shared.base_model import BaseModel


class PaymentMethod(BaseModel):
    TYPE_CHOICES = [
        ("credit_card", "Credit Card"),
        ("debit_card", "Debit Card"),
        ("bank_transfer", "Bank Transfer"),
        ("vnpay", "VNPay"),
        ("momo", "MoMo"),
        ("zalopay", "ZaloPay"),
        ("cod", "Cash on Delivery"),
        ("stripe", "Stripe"),
    ]
    user_id = models.UUIDField(db_index=True)
    method_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    details = models.JSONField(default=dict)   # masked card number, bank name, etc.
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "payment_methods"

    def __str__(self):
        return f"{self.user_id} - {self.method_type}"


class Transaction(BaseModel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
        ("partially_refunded", "Partially Refunded"),
    ]
    order_id = models.UUIDField(db_index=True)
    user_id = models.UUIDField(db_index=True)
    payment_method = models.ForeignKey(
        PaymentMethod, null=True, blank=True, on_delete=models.SET_NULL
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="VND")
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default="pending", db_index=True)

    # Gateway-specific
    gateway_transaction_id = models.CharField(max_length=255, blank=True, db_index=True)
    gateway_response = models.JSONField(default=dict)
    failure_reason = models.TextField(blank=True)

    paid_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    refunded_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "transactions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"TXN-{self.id} ({self.status})"
