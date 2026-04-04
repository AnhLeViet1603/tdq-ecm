from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from shared.base_model import BaseModel


class Review(BaseModel):
    product_id = models.UUIDField(db_index=True)
    user_id = models.UUIDField(db_index=True)
    user_name = models.CharField(max_length=255, blank=True)
    order_id = models.UUIDField(null=True, blank=True)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    helpful_count = models.PositiveIntegerField(default=0)
    reply = models.TextField(blank=True)          # seller reply
    replied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "reviews"
        # unique_together = ("product_id", "user_id", "order_id")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Review({self.product_id}) rating={self.rating}"


class ReviewMedia(BaseModel):
    MEDIA_TYPES = [("image", "Image"), ("video", "Video")]
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="media")
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES, default="image")
    url = models.URLField()
    thumbnail_url = models.URLField(blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "review_media"
        ordering = ["sort_order"]
