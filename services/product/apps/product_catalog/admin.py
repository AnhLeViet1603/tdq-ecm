from django.contrib import admin
from .models import Category, Attribute, Product, ProductAttribute


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "parent", "is_active", "sort_order"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "sku", "category", "base_price", "is_active", "created_at"]
    list_filter = ["is_active", "category"]
    search_fields = ["name", "sku"]
    prepopulated_fields = {"slug": ("name",)}


admin.site.register(Attribute)
admin.site.register(ProductAttribute)
