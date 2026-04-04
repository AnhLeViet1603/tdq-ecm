"""
shared/permissions.py
─────────────────────
Reusable DRF permission classes cho tất cả downstream microservices.
Hoạt động với JWTUser (từ ServiceJWTAuthentication) — không cần DB query.
"""

from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """Chỉ cho phép user có role 'admin' trong JWT payload."""
    message = "Chỉ admin mới có quyền thực hiện thao tác này."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # JWTUser.roles là list string, Django User.is_staff là bool
        if hasattr(user, "has_role"):
            return user.has_role("admin")
        return bool(user.is_staff and user.is_superuser)


class IsStaffRole(BasePermission):
    """Chỉ cho phép user có role 'staff' (employee) trong JWT payload."""
    message = "Chỉ nhân viên mới có quyền thực hiện thao tác này."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if hasattr(user, "has_role"):
            return user.has_role("staff")
        return bool(user.is_staff)


class IsAdminOrStaff(BasePermission):
    """Cho phép user có role 'admin' hoặc 'staff' (employee)."""
    message = "Chỉ admin hoặc nhân viên mới có quyền thực hiện thao tác này."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if hasattr(user, "has_role"):
            return user.has_role("admin") or user.has_role("staff")
        return bool(user.is_staff)


class IsOwnerOrAdminOrStaff(BasePermission):
    """
    Cho phép:
    - Admin / Staff: toàn quyền
    - Customer: chỉ xem object của chính mình (cần object có user_id / owner field)
    """
    message = "Bạn không có quyền truy cập tài nguyên này."

    owner_field = "user_id"  # Override trong view nếu cần

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        # Admin / Staff có full access
        if hasattr(user, "has_role"):
            if user.has_role("admin") or user.has_role("staff"):
                return True
        elif user.is_staff:
            return True

        # Owner check
        field = getattr(self, "owner_field", "user_id")
        return str(getattr(obj, field, None)) == str(user.id)
