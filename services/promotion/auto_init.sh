#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, timedelta
from uuid import uuid4

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/app')
django.setup()

from apps.promotion.models import Coupon, Discount, UsageLimit


def create_sample_coupons():
    """Create sample coupons for testing"""

    coupons_data = [
        {
            'code': 'WELCOME10',
            'name': 'Welcome Discount',
            'description': 'Giảm 10% cho đơn hàng đầu tiên. Áp dụng cho tất cả sản phẩm.',
            'coupon_type': 'percentage',
            'value': 10,
            'min_order_amount': 0,
            'max_discount_amount': 200000,
            'total_limit': 1000,
            'per_user_limit': 1,
        },
        {
            'code': 'FREESHIP',
            'name': 'Free Shipping',
            'description': 'Miễn phí giao hàng cho đơn hàng từ 500k. Áp dụng toàn bộ sản phẩm.',
            'coupon_type': 'free_shipping',
            'value': 30000,
            'min_order_amount': 500000,
            'max_discount_amount': None,
            'total_limit': None,
            'per_user_limit': 5,
        },
        {
            'code': 'SALE20',
            'name': 'Super Sale 20%',
            'description': 'Giảm 20% cho đơn hàng từ 2 triệu. Không giới hạn giảm giá.',
            'coupon_type': 'percentage',
            'value': 20,
            'min_order_amount': 2000000,
            'max_discount_amount': None,
            'total_limit': 500,
            'per_user_limit': 2,
        },
        {
            'code': 'IPHONE15',
            'name': 'iPhone 15 Deal',
            'description': 'Giảm 500k cho iPhone 15 Series. Áp dụng cho các sản phẩm iPhone.',
            'coupon_type': 'fixed',
            'value': 500000,
            'min_order_amount': 10000000,
            'max_discount_amount': 500000,
            'total_limit': 100,
            'per_user_limit': 1,
            'applicable_products': ['00000000-0000-0000-0000-000000000001']
        },
        {
            'code': 'MACBOOK',
            'name': 'MacBook Promotion',
            'description': 'Giảm 1 triệu cho MacBook Series. Duy nhất hôm nay!',
            'coupon_type': 'fixed',
            'value': 1000000,
            'min_order_amount': 20000000,
            'max_discount_amount': 1000000,
            'total_limit': 50,
            'per_user_limit': 1,
            'applicable_products': ['00000000-0000-0000-0000-000000000007']
        },
        {
            'code': 'TECH5',
            'name': 'Tech Lover 5%',
            'description': 'Giảm 5% cho tất cả sản phẩm công nghệ. Không điều kiện.',
            'coupon_type': 'percentage',
            'value': 5,
            'min_order_amount': 100000,
            'max_discount_amount': 100000,
            'total_limit': None,
            'per_user_limit': 10,
        },
        {
            'code': 'VIP100',
            'name': 'VIP Customer',
            'description': 'Giảm 100k cho đơn hàng từ 1 triệu. Coupon đặc biệt.',
            'coupon_type': 'fixed',
            'value': 100000,
            'min_order_amount': 1000000,
            'max_discount_amount': 100000,
            'total_limit': 200,
            'per_user_limit': 3,
        },
        {
            'code': 'AUDIO50',
            'name': 'Audio Equipment Sale',
            'description': 'Giảm 50k cho thiết bị âm thanh. Tai nghe, loa...',
            'coupon_type': 'fixed',
            'value': 50000,
            'min_order_amount': 200000,
            'max_discount_amount': 50000,
            'total_limit': None,
            'per_user_limit': 5,
            'applicable_categories': ['audio', 'headphones']
        }
    ]

    coupons_created = 0

    for coupon_data in coupons_data:
        # Extract applicable products/categories
        applicable_products = coupon_data.pop('applicable_products', [])
        applicable_categories = coupon_data.pop('applicable_categories', [])

        # Extract discount data
        value = coupon_data.pop('value')
        min_order_amount = coupon_data.pop('min_order_amount')
        max_discount_amount = coupon_data.pop('max_discount_amount')

        # Extract usage limit data
        total_limit = coupon_data.pop('total_limit')
        per_user_limit = coupon_data.pop('per_user_limit')

        # Create coupon
        coupon = Coupon.objects.create(
            **coupon_data,
            applicable_products=applicable_products,
            applicable_categories=applicable_categories,
            starts_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=90)  # Valid for 90 days
        )

        # Create discount
        Discount.objects.create(
            coupon=coupon,
            value=value,
            min_order_amount=min_order_amount,
            max_discount_amount=max_discount_amount
        )

        # Create usage limit
        UsageLimit.objects.create(
            coupon=coupon,
            total_limit=total_limit,
            per_user_limit=per_user_limit,
            used_count=0
        )

        coupons_created += 1
        print(f"✓ Created coupon: {coupon.code} - {coupon.name}")

    print(f"\n✅ Created {coupons_created} sample coupons")


if __name__ == '__main__':
    print("🌱 Starting promotion data initialization...")
    create_sample_coupons()
    print("🎉 Promotion initialization completed!")
