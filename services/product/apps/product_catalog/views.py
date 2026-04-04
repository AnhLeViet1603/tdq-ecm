from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from shared.permissions import IsAdminOrStaff
from shared.responses import success_response, created_response, error_response

from .models import Category, Attribute, Product, ProductAttribute
from .serializers import (
    CategorySerializer, CategoryDetailSerializer,
    AttributeSerializer,
    ProductSerializer, ProductListSerializer,
    ProductAttributeSerializer, ProductAttributeWriteSerializer,
)


# ──────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


def _is_admin_or_staff(request) -> bool:
    user = request.user
    if not user or not user.is_authenticated:
        return False
    if hasattr(user, "has_role"):
        return user.has_role("admin") or user.has_role("staff")
    return bool(user.is_staff)


# ──────────────────────────────────────────────────────────────
#  Category CRUD
# ──────────────────────────────────────────────────────────────

class CategoryViewSet(viewsets.ModelViewSet):
    """
    list/retrieve  — public (không cần đăng nhập)
    create/update/delete — Admin hoặc Staff
    """
    filter_backends   = [filters.SearchFilter, filters.OrderingFilter]
    search_fields     = ["name", "slug", "description"]
    ordering_fields   = ["sort_order", "name", "created_at"]
    ordering          = ["sort_order", "name"]

    def get_queryset(self):
        qs = Category.objects.prefetch_related("children")
        # Admin/Staff xem cả inactive
        if _is_admin_or_staff(self.request):
            return qs.all()
        return qs.filter(is_active=True)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CategoryDetailSerializer
        return CategorySerializer

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminOrStaff()]

    # ── /categories/tree/ — toàn bộ cây danh mục root ─────────
    @action(detail=False, methods=["get"], url_path="tree")
    def tree(self, request):
        roots = self.get_queryset().filter(parent__isnull=True)
        data  = CategoryDetailSerializer(roots, many=True).data
        return success_response(data=data, message="Category tree fetched.")

    # ── /categories/{id}/products/ — sản phẩm theo danh mục ───
    @action(detail=True, methods=["get"], url_path="products")
    def products(self, request, pk=None):
        category = self.get_object()
        qs = Product.objects.filter(category=category)
        if not _is_admin_or_staff(request):
            qs = qs.filter(is_active=True)
        serializer = ProductListSerializer(qs, many=True)
        return success_response(data=serializer.data)

    def perform_create(self, serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return created_response(
            data=serializer.data,
            message="Danh mục đã được tạo thành công.",
        )

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            data=serializer.data,
            message="Danh mục đã được cập nhật.",
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        name     = instance.name
        instance.delete()
        return success_response(message=f"Danh mục '{name}' đã bị xóa.")


# ──────────────────────────────────────────────────────────────
#  Attribute CRUD
# ──────────────────────────────────────────────────────────────

class AttributeViewSet(viewsets.ModelViewSet):
    """
    list/retrieve  — đăng nhập
    create/update/delete — Admin hoặc Staff
    """
    queryset        = Attribute.objects.all().order_by("name")
    serializer_class = AttributeSerializer
    filter_backends = [filters.SearchFilter]
    search_fields   = ["name"]

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminOrStaff()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return created_response(
            data=serializer.data,
            message="Thuộc tính đã được tạo.",
        )

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message="Thuộc tính đã được cập nhật.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message="Thuộc tính đã bị xóa.")


# ──────────────────────────────────────────────────────────────
#  Product CRUD
# ──────────────────────────────────────────────────────────────

class ProductViewSet(viewsets.ModelViewSet):
    """
    list/retrieve  — public
    create/update/delete — Admin hoặc Staff

    Query params (list):
      ?search=...        tìm theo name / sku / description
      ?category=<slug>   lọc theo danh mục
      ?is_active=true    lọc theo trạng thái (Admin/Staff thấy inactive)
      ?ordering=base_price,-created_at
      ?min_price=...     giá tối thiểu
      ?max_price=...     giá tối đa
    """
    filter_backends  = [filters.SearchFilter, filters.OrderingFilter]
    search_fields    = ["name", "sku", "description", "tags"]
    ordering_fields  = ["base_price", "compare_price", "created_at", "name"]
    ordering         = ["-created_at"]

    def get_queryset(self):
        qs = Product.objects.select_related("category").prefetch_related(
            "attributes__attribute"
        )
        # Admin/Staff xem cả inactive
        if not _is_admin_or_staff(self.request):
            qs = qs.filter(is_active=True)

        params = self.request.query_params

        # Filter by category slug
        category = params.get("category")
        if category:
            qs = qs.filter(category__slug=category)

        # Filter by is_active (Admin/Staff only)
        is_active = params.get("is_active")
        if is_active is not None and _is_admin_or_staff(self.request):
            qs = qs.filter(is_active=is_active.lower() == "true")

        # Price range
        min_price = params.get("min_price")
        max_price = params.get("max_price")
        if min_price:
            qs = qs.filter(base_price__gte=min_price)
        if max_price:
            qs = qs.filter(base_price__lte=max_price)

        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        return ProductSerializer

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminOrStaff()]

    # ── Override responses ─────────────────────────────────────
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return created_response(
            data=serializer.data,
            message="Sản phẩm đã được tạo thành công.",
        )

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            data=serializer.data,
            message="Sản phẩm đã được cập nhật.",
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        name     = instance.name
        instance.delete()
        return success_response(message=f"Sản phẩm '{name}' đã bị xóa.")

    # ── /products/{id}/toggle-active/ ─────────────────────────
    @action(
        detail=True, methods=["post"],
        url_path="toggle-active",
        permission_classes=[IsAuthenticated, IsAdminOrStaff],
    )
    def toggle_active(self, request, pk=None):
        product = self.get_object()
        product.is_active = not product.is_active
        product.save(update_fields=["is_active"])
        state = "kích hoạt" if product.is_active else "ẩn"
        return success_response(
            data={"id": str(product.id), "is_active": product.is_active},
            message=f"Sản phẩm đã được {state}.",
        )

    # ── /products/{id}/attributes/ — quản lý attributes ───────
    @action(
        detail=True, methods=["get", "post", "delete"],
        url_path="attributes",
        permission_classes=[IsAuthenticated, IsAdminOrStaff],
    )
    def manage_attributes(self, request, pk=None):
        product = self.get_object()

        if request.method == "GET":
            attrs = product.attributes.select_related("attribute").all()
            return success_response(
                data=ProductAttributeSerializer(attrs, many=True).data
            )

        if request.method == "POST":
            serializer = ProductAttributeWriteSerializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            product.attributes.all().delete()
            ProductAttribute.objects.bulk_create([
                ProductAttribute(product=product, **item)
                for item in serializer.validated_data
            ])
            attrs = product.attributes.select_related("attribute").all()
            return success_response(
                data=ProductAttributeSerializer(attrs, many=True).data,
                message="Thuộc tính sản phẩm đã được cập nhật.",
            )

        if request.method == "DELETE":
            product.attributes.all().delete()
            return success_response(message="Đã xóa toàn bộ thuộc tính sản phẩm.")
