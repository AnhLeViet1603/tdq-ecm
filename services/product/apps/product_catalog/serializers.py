from rest_framework import serializers
from .models import Category, Attribute, Product, ProductAttribute


# ──────────────────────────────────────────────────────────────
#  Category
# ──────────────────────────────────────────────────────────────

class CategorySerializer(serializers.ModelSerializer):
    children_count = serializers.SerializerMethodField(read_only=True)
    product_count  = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = Category
        fields = [
            "id", "name", "slug", "parent", "description", "image",
            "is_active", "sort_order", "children_count", "product_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_children_count(self, obj):
        return obj.children.count()

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class CategoryDetailSerializer(CategorySerializer):
    """Kèm danh sách children khi xem chi tiết."""
    children = CategorySerializer(many=True, read_only=True)

    class Meta(CategorySerializer.Meta):
        fields = CategorySerializer.Meta.fields + ["children"]


# ──────────────────────────────────────────────────────────────
#  Attribute
# ──────────────────────────────────────────────────────────────

class AttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Attribute
        fields = ["id", "name", "values", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


# ──────────────────────────────────────────────────────────────
#  ProductAttribute (embedded trong Product)
# ──────────────────────────────────────────────────────────────

class ProductAttributeSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source="attribute.name", read_only=True)

    class Meta:
        model  = ProductAttribute
        fields = ["id", "attribute", "attribute_name", "value"]
        read_only_fields = ["id"]


class ProductAttributeWriteSerializer(serializers.ModelSerializer):
    """Dùng khi tạo/cập nhật attribute cho một product."""
    class Meta:
        model  = ProductAttribute
        fields = ["attribute", "value"]


# ──────────────────────────────────────────────────────────────
#  Product — List (gọn nhẹ)
# ──────────────────────────────────────────────────────────────

class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model  = Product
        fields = [
            "id", "sku", "name", "slug",
            "category", "category_name",
            "base_price", "compare_price",
            "images", "is_active",
            "created_at",
        ]


# ──────────────────────────────────────────────────────────────
#  Product — Detail + Write
# ──────────────────────────────────────────────────────────────

class ProductSerializer(serializers.ModelSerializer):
    attributes    = ProductAttributeSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    # Write-only: cho phép gửi attributes khi create/update
    set_attributes = ProductAttributeWriteSerializer(
        many=True, write_only=True, required=False,
        help_text="Danh sách {attribute, value} để gán cho sản phẩm.",
    )

    class Meta:
        model  = Product
        fields = [
            "id", "sku", "name", "slug", "description",
            "category", "category_name",
            "base_price", "compare_price",
            "images", "tags",
            "is_active", "meta_title", "meta_description",
            "attributes", "set_attributes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def _save_attributes(self, product, attrs_data):
        if attrs_data is None:
            return
        # Xóa cũ, thêm mới
        product.attributes.all().delete()
        ProductAttribute.objects.bulk_create([
            ProductAttribute(product=product, **item) for item in attrs_data
        ])

    def create(self, validated_data):
        attrs_data = validated_data.pop("set_attributes", None)
        product    = super().create(validated_data)
        self._save_attributes(product, attrs_data)
        return product

    def update(self, instance, validated_data):
        attrs_data = validated_data.pop("set_attributes", None)
        product    = super().update(instance, validated_data)
        self._save_attributes(product, attrs_data)
        return product
