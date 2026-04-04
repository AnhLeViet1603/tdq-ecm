from django.db import models
from shared.base_model import BaseModel


class Category(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=300, unique=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )
    description = models.TextField(blank=True)
    image = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "categories"
        ordering = ["sort_order", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Attribute(BaseModel):
    name = models.CharField(max_length=100)  # Color, Size, Material
    values = models.JSONField(default=list)   # ["Red", "Blue", "XL"]

    class Meta:
        db_table = "attributes"

    def __str__(self):
        return self.name


class Product(BaseModel):
    sku = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=500)
    slug = models.SlugField(max_length=600, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="products"
    )
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    compare_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    images = models.JSONField(default=list)   # list of image URLs
    tags = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)

    class Meta:
        db_table = "products"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class ProductAttribute(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="attributes")
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

    class Meta:
        db_table = "product_attributes"
        unique_together = ("product", "attribute")

    def __str__(self):
        return f"{self.product.name} - {self.attribute.name}: {self.value}"
