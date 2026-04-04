from django.db import models
from shared.base_model import BaseModel


class Coupon(BaseModel):
    TYPE_CHOICES = [
        ("percentage", "Percentage Discount"),
        ("fixed", "Fixed Amount Discount"),
        ("free_shipping", "Free Shipping"),
    ]
    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    coupon_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField()
    expires_at = models.DateTimeField(null=True, blank=True)
    applicable_products = models.JSONField(default=list)   # empty = all products
    applicable_categories = models.JSONField(default=list) # empty = all categories

    class Meta:
        db_table = "coupons"

    def __str__(self):
        return self.code


class Discount(BaseModel):
    coupon = models.OneToOneField(Coupon, on_delete=models.CASCADE, related_name="discount")
    value = models.DecimalField(max_digits=10, decimal_places=2)              # % or VND
    min_order_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_discount_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "discounts"

    def __str__(self):
        return f"{self.coupon.code}: {self.value}"


class UsageLimit(BaseModel):
    coupon = models.OneToOneField(Coupon, on_delete=models.CASCADE, related_name="usage_limit")
    total_limit = models.PositiveIntegerField(null=True, blank=True)  # None = unlimited
    per_user_limit = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "usage_limits"

    @property
    def is_exhausted(self):
        return self.total_limit is not None and self.used_count >= self.total_limit

    def __str__(self):
        return f"{self.coupon.code}: {self.used_count}/{self.total_limit or 'unlimited'}"
