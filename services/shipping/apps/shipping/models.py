from django.db import models
from shared.base_model import BaseModel


class Carrier(BaseModel):
    name = models.CharField(max_length=255)   # GHN, GHTK, ViettelPost, J&T
    code = models.CharField(max_length=50, unique=True)
    api_endpoint = models.URLField(blank=True)
    api_key = models.CharField(max_length=255, blank=True)
    tracking_url_template = models.URLField(blank=True)  # https://tracking.ghn.dev/?order_code={tracking_number}
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "carriers"

    def __str__(self):
        return self.name


class Shipment(BaseModel):
    STATUS_CHOICES = [
        ("pending", "Pending Pickup"),
        ("picked_up", "Picked Up"),
        ("in_transit", "In Transit"),
        ("out_for_delivery", "Out for Delivery"),
        ("delivered", "Delivered"),
        ("failed_delivery", "Failed Delivery"),
        ("returned", "Returned to Sender"),
        ("cancelled", "Cancelled"),
    ]
    order_id = models.UUIDField(db_index=True)
    carrier = models.ForeignKey(
        Carrier, null=True, blank=True, on_delete=models.SET_NULL, related_name="shipments"
    )
    tracking_number = models.CharField(max_length=255, unique=True, db_index=True)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default="pending", db_index=True)
    sender_address = models.JSONField()
    recipient_address = models.JSONField()
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    weight_grams = models.PositiveIntegerField(default=0)
    cod_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estimated_delivery = models.DateField(null=True, blank=True)
    actual_delivery = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "shipments"
        ordering = ["-created_at"]

    def __str__(self):
        return self.tracking_number


class TrackingLog(BaseModel):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="logs")
    status = models.CharField(max_length=25)
    location = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField()

    class Meta:
        db_table = "tracking_logs"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.shipment.tracking_number} @ {self.timestamp}: {self.status}"
