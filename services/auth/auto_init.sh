#!/bin/bash
# ════════════════════════════════════════════════════════════
# AUTO-INITIALIZATION SCRIPT
# Runs automatically on first container startup
# Populates all databases with sample data
# ════════════════════════════════════════════════════════════

set -e

echo "🚀 Checking if database needs initialization..."

# Check if already initialized
if [ -f "/app/.initialized" ]; then
    echo "✅ Database already initialized, skipping..."
    exit 0
fi

echo "📝 Initializing database with sample data..."

# Wait for database to be ready
echo "⏳ Waiting for database..."
while ! python manage.py shell -c "from django.db import connection; connection.ensure_connection()" 2>/dev/null; do
    echo "Database not ready, waiting..."
    sleep 2
done

# Import models and populate data
python manage.py shell << 'EOF'
import os
import sys
import django
django.setup()

from apps.authentication.models import User, Role
from datetime import datetime, timedelta
import random
import uuid

print("🔐 Creating roles and users...")

# Create roles
for role_name in ['admin', 'staff', 'customer']:
    if not Role.objects.filter(name=role_name).exists():
        role = Role.objects.create(name=role_name, description=f'{role_name.capitalize()} role')
        print(f"  ✅ Created role: {role.name}")

# Create admin user
if not User.objects.filter(email='admin@shopvn.com').exists():
    admin = User.objects.create_superuser(
        email='admin@shopvn.com',
        full_name='Admin User',
        password='admin123',
        phone='0901234567'
    )
    admin.roles.set([Role.objects.get(name='admin')])
    admin.is_active = True
    admin.save()
    print("  ✅ Created admin user: admin@shopvn.com / admin123")

# Create sample users
first_names = ['Nam', 'Lan', 'Hùng', 'Mai', 'Tuấn', 'Hương', 'Minh', 'Thu']
last_names = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ']

for i in range(10):
    email = f"user{i+1}@example.com"
    if not User.objects.filter(email=email).exists():
        full_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        user = User.objects.create_user(
            email=email,
            full_name=full_name,
            password='password123',
            phone=f"0{random.randint(900000000, 999999999)}"
        )
        # Assign random role
        if random.choice([True, False]):
            user.roles.set([Role.objects.get(name='staff')])
        else:
            user.roles.set([Role.objects.get(name='customer')])
        user.is_active = True
        user.save()
        print(f"  ✅ Created user: {email}")

print("✅ Auth database initialized!")
EOF

# Mark as initialized
touch /app/.initialized

echo "🎉 Database initialization completed!"
echo "📝 Login credentials:"
echo "   Admin: admin@shopvn.com / admin123"
echo "   Users: user1-10@example.com / password123"
