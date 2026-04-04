"""
Management command: seed_admin
──────────────────────────────
Thực hiện 2 việc khi auth service khởi động lần đầu:
  1. Seed các Role cơ bản: admin, staff, customer
  2. Tạo tài khoản superuser và gán role "admin"

Idempotent — chạy nhiều lần không bị duplicate.

Env vars:
    ADMIN_EMAIL     (default: admin@shopvn.com)
    ADMIN_PASSWORD  (default: Admin@123456)
    ADMIN_FULL_NAME (default: Super Admin)
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.authentication.models import Role

User = get_user_model()

# Các role mặc định của hệ thống
DEFAULT_ROLES = [
    {"name": "admin",    "description": "Quản trị viên hệ thống — toàn quyền"},
    {"name": "staff",    "description": "Nhân viên — quyền quản lý nội dung"},
    {"name": "customer", "description": "Khách hàng — quyền mua sắm"},
]


class Command(BaseCommand):
    help = "Seed default roles and the initial admin superuser account."

    def handle(self, *args, **kwargs):
        # ── 1. Seed default roles ──────────────────────────────
        self.stdout.write("  Seeding default roles...")
        for role_data in DEFAULT_ROLES:
            role, created = Role.objects.get_or_create(
                name=role_data["name"],
                defaults={"description": role_data["description"]},
            )
            status = "created" if created else "exists"
            self.stdout.write(f"    Role '{role.name}': {status}")

        admin_role = Role.objects.get(name="admin")

        # ── 2. Seed superuser ──────────────────────────────────
        email     = os.environ.get("ADMIN_EMAIL",     "admin@shopvn.com")
        password  = os.environ.get("ADMIN_PASSWORD",  "Admin@123456")
        full_name = os.environ.get("ADMIN_FULL_NAME", "Super Admin")

        user, created = User.objects.get_or_create(
            email=email,
            defaults={"full_name": full_name, "is_staff": True, "is_superuser": True},
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(
                f"  Superuser created → {email}"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f"  Superuser '{email}' already exists."
            ))

        # ── 3. Ensure admin role is assigned ──────────────────
        if not user.roles.filter(name="admin").exists():
            user.roles.add(admin_role)
            self.stdout.write(self.style.SUCCESS(
                f"  Role 'admin' assigned to {email}"
            ))
        else:
            self.stdout.write(f"  Role 'admin' already assigned to {email}.")

        # Đảm bảo flags đúng dù user đã tồn tại trước
        if not (user.is_staff and user.is_superuser):
            user.is_staff = True
            user.is_superuser = True
            user.save(update_fields=["is_staff", "is_superuser"])
            self.stdout.write("  Fixed is_staff / is_superuser flags.")

        self.stdout.write(self.style.SUCCESS("[seed_admin] Done."))
