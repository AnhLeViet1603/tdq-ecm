#!/usr/bin/env python
import os
import sys
import django
import random
from datetime import datetime, timedelta
from uuid import uuid4

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/app')
django.setup()

from apps.order.models import Order, OrderItem, OrderHistory
from django.db import transaction


def create_sample_orders():
    """Create sample orders for testing"""

    # Sample user IDs (these should match auth service users)
    user_ids = [
        '11111111-1111-1111-1111-111111111111',
        '22222222-2222-2222-2222-222222222222',
        '33333333-3333-3333-3333-333333333333',
        '44444444-4444-4444-4444-444444444444',
        '55555555-5555-5555-5555-555555555555',
    ]

    # Sample product data (should match product service products)
    products = [
        {'id': '00000000-0000-0000-0000-000000000001', 'name': 'iPhone 15 Pro Max 256GB', 'price': 32990000, 'sku': 'IP15PM-256-BLK'},
        {'id': '00000000-0000-0000-0000-000000000002', 'name': 'MacBook Air M2 13.6"', 'price': 26990000, 'sku': 'MBA-M2-13-SLV'},
        {'id': '00000000-0000-0000-0000-000000000003', 'name': 'AirPods Pro 2 USB-C', 'price': 5990000, 'sku': 'APP2-USB-C'},
        {'id': '00000000-0000-0000-0000-000000000004', 'name': 'Samsung Galaxy S24 Ultra', 'price': 28990000, 'sku': 'S24U-512-TIT'},
        {'id': '00000000-0000-0000-0000-000000000005', 'name': 'iPad Air 5 M1 64GB Wi-Fi', 'price': 16990000, 'sku': 'IPA5-M1-64-BLU'},
    ]

    # Sample addresses
    addresses = [
        {
            'full_name': 'Nguyễn Văn An',
            'phone': '0901234567',
            'province': 'Hà Nội',
            'district': 'Cầu Giấy',
            'ward': 'Dịch Vọng',
            'address_line': '123 Đường Nguyễn Phong Sắc',
            'address_type': 'home'
        },
        {
            'full_name': 'Trần Thị Bình',
            'phone': '0912345678',
            'province': 'TP. Hồ Chí Minh',
            'district': 'Quận 1',
            'ward': 'Bến Nghé',
            'address_line': '456 Đường Lê Lợi',
            'address_type': 'office'
        },
        {
            'full_name': 'Lê Văn Cường',
            'phone': '0923456789',
            'province': 'Đà Nẵng',
            'district': 'Hải Châu',
            'ward': 'Thạch Thang',
            'address_line': '789 Đường Trần Phú',
            'address_type': 'home'
        }
    ]

    payment_methods = ['credit_card', 'momo', 'zalopay', 'bank_transfer', 'cod']
    shipping_methods = ['express', 'standard', 'economy']
    statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']

    orders_created = 0

    with transaction.atomic():
        for i in range(15):  # Create 15 sample orders
            user_id = random.choice(user_ids)
            status = random.choice(statuses)

            # Create order number
            order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{i+1:04d}"

            # Generate random order items (1-3 items per order)
            num_items = random.randint(1, 3)
            selected_products = random.sample(products, num_items)

            # Calculate totals
            subtotal = sum(p['price'] * random.randint(1, 2) for p in selected_products)
            discount_amount = random.choice([0, 0, 0, 50000, 100000, 200000])
            shipping_fee = random.choice([0, 15000, 30000])
            tax_amount = subtotal * 0.1  # 10% tax
            total_amount = subtotal - discount_amount + shipping_fee + tax_amount

            # Create order
            order = Order.objects.create(
                user_id=user_id,
                order_number=order_number,
                status=status,
                subtotal=subtotal,
                discount_amount=discount_amount,
                shipping_fee=shipping_fee,
                tax_amount=tax_amount,
                total_amount=total_amount,
                payment_method=random.choice(payment_methods),
                shipping_method=random.choice(shipping_methods),
                shipping_address=random.choice(addresses),
                billing_address=random.choice(addresses),
                notes=random.choice(['', 'Giao hàng giờ hành chính', 'Gọi trước khi giao']),
                created_at=datetime.now() - timedelta(days=random.randint(1, 30))
            )

            # Create order items
            for product in selected_products:
                quantity = random.randint(1, 2)
                unit_price = product['price']
                discount = random.choice([0, 0, 50000, 100000])
                total_price = (unit_price - discount) * quantity

                OrderItem.objects.create(
                    order=order,
                    product_id=product['id'],
                    product_sku=product['sku'],
                    product_name=product['name'],
                    product_image=f'https://example.com/products/{product["sku"]}.jpg',
                    unit_price=unit_price,
                    quantity=quantity,
                    discount_amount=discount,
                    total_price=total_price,
                    attributes={'color': random.choice(['Đen', 'Trắng', 'Xanh']), 'warranty': '12 tháng'}
                )

            # Create order history
            if status != 'pending':
                OrderHistory.objects.create(
                    order=order,
                    previous_status='pending',
                    new_status=status,
                    changed_by=user_id,
                    note=f'Order changed to {status}'
                )

            orders_created += 1
            print(f"✓ Created order: {order_number} ({status})")

    print(f"\n✅ Created {orders_created} sample orders")


if __name__ == '__main__':
    print("🌱 Starting order data initialization...")
    create_sample_orders()
    print("🎉 Order initialization completed!")
