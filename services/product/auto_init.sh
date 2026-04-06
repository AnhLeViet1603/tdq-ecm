#!/bin/bash
# Auto-initialization script for Product Service
set -e

echo "🚀 Product Service - Auto-initialization"

if [ -f "/app/.initialized" ]; then
    echo "✅ Already initialized"
    exit 0
fi

echo "⏳ Waiting for database..."
while ! python manage.py shell -c "from django.db import connection; connection.ensure_connection()" 2>/dev/null; do
    sleep 2
done

python manage.py shell << 'EOF'
from apps.product_catalog.models import Category, Product
import random

print("📦 Creating categories and products...")

category_data = [
    {'name': 'Điện thoại', 'slug': 'dien-thoai', 'description': 'Điện thoại thông minh'},
    {'name': 'iPhone', 'slug': 'iphone', 'description': 'iPhone Apple chính hãng'},
    {'name': 'Samsung', 'slug': 'samsung', 'description': 'Samsung Galaxy'},
    {'name': 'Laptop', 'slug': 'laptop', 'description': 'Laptop công việc'},
    {'name': 'MacBook', 'slug': 'macbook', 'description': 'MacBook Apple'},
    {'name': 'Dell', 'slug': 'dell', 'description': 'Laptop Dell'},
]

for cat in category_data:
    if not Category.objects.filter(slug=cat['slug']).exists():
        category = Category.objects.create(
            name=cat['name'],
            slug=cat['slug'],
            description=cat['description'],
            is_active=True
        )
        print(f"  ✅ {category.name}")

product_data = [
    {'name': 'iPhone 15 Pro Max 256GB', 'slug': 'iphone-15-pro-max-256gb', 'category': 'iphone', 'price': 34990000},
    {'name': 'iPhone 15 128GB', 'slug': 'iphone-15-128gb', 'category': 'iphone', 'price': 21990000},
    {'name': 'Samsung Galaxy S24 Ultra 512GB', 'slug': 'samsung-galaxy-s24-ultra', 'category': 'samsung', 'price': 32990000},
    {'name': 'MacBook Pro 16" M3 Pro', 'slug': 'macbook-pro-16-m3-pro', 'category': 'macbook', 'price': 69990000},
    {'name': 'AirPods Pro 2', 'slug': 'airpods-pro-2', 'category': 'tai-nghe', 'price': 4990000},
]

for prod in product_data:
    if not Product.objects.filter(slug=prod['slug']).exists():
        try:
            category = Category.objects.get(slug=prod['category'])
            Product.objects.create(
                sku=f"SKU-{prod['category'].upper()}-{random.randint(1000, 9999)}",
                name=prod['name'],
                slug=prod['slug'],
                description=f"Sản phẩm {prod['name']} chất lượng cao",
                category=category,
                base_price=prod['price'],
                compare_price=int(prod['price'] * 1.1),
                images=[f"https://via.placeholder.com/400x400?text={prod['name'].replace(' ', '+')}"],
                tags=['new', 'hot'],
                is_active=True
            )
            print(f"  ✅ {prod['name']}")
        except Exception as e:
            print(f"  ⚠️ Skipped {prod['name']}: {e}")

print("✅ Product service initialized!")
EOF

touch /app/.initialized
