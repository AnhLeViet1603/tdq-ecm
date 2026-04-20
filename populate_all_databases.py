#!/usr/bin/env python3
"""
Populate all service databases with comprehensive sample data
"""
import os
import sys
import django
import random
import uuid
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def populate_auth_db():
    """Populate auth database with sample users"""
    print("🔐 Populating Auth database...")
    # Import after setting up Django
    if os.path.exists('services/auth'):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'services.auth.config.settings')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    django.setup()

    from apps.authentication.models import User

    # Create admin user
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@shopvn.com',
            password='admin123',
            first_name='Admin',
            last_name='User',
            role='admin',
            is_active=True,
            is_verified=True
        )
        print(f"   ✅ Created admin user: {admin.username}")

    # Create sample users
    roles = ['customer', 'staff', 'admin']
    first_names = ['Nam', 'Lan', 'Hùng', 'Mai', 'Tuấn', 'Hương', 'Minh', 'Thu']
    last_names = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ']

    for i in range(10):
        username = f"user{i+1}"
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                email=f"user{i+1}@example.com",
                password='password123',
                first_name=random.choice(first_names),
                last_name=random.choice(last_names),
                role=random.choice(roles),
                phone=f"0{random.randint(900000000, 999999999)}",
                is_active=True,
                is_verified=True
            )
            print(f"   ✅ Created user: {user.username} ({user.role})")

    print("   ✅ Auth database populated successfully!\n")

def populate_product_db():
    """Populate product database with sample products and categories"""
    print("📦 Populating Product database...")
    if os.path.exists('services/product'):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'services.product.config.settings')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    django.setup()

    from apps.product_catalog.models import Category, Attribute, Product

    # Create categories
    category_data = [
        {'name': 'Điện thoại', 'slug': 'dien-thoai', 'description': 'Điện thoại thông minh', 'parent': None},
        {'name': 'iPhone', 'slug': 'iphone', 'description': 'iPhone Apple chính hãng', 'parent': 'dien-thoai'},
        {'name': 'Samsung', 'slug': 'samsung', 'description': 'Samsung Galaxy', 'parent': 'dien-thoai'},
        {'name': 'Laptop', 'slug': 'laptop', 'description': 'Laptop công việc', 'parent': None},
        {'name': 'MacBook', 'slug': 'macbook', 'description': 'MacBook Apple', 'parent': 'laptop'},
        {'name': 'Dell', 'slug': 'dell', 'description': 'Laptop Dell', 'parent': 'laptop'},
        {'name': 'Máy tính bảng', 'slug': 'may-tinh-bang', 'description': 'Máy tính bảng Tablet', 'parent': None},
        {'name': 'iPad', 'slug': 'ipad', 'description': 'iPad Apple chính hãng', 'parent': 'may-tinh-bang'},
        {'name': 'Samsung Tablet', 'slug': 'samsung-tablet', 'description': 'Samsung Galaxy Tab', 'parent': 'may-tinh-bang'},
        {'name': 'Phụ kiện', 'slug': 'phu-kien', 'description': 'Phụ kiện công nghệ', 'parent': None},
        {'name': 'Tai nghe', 'slug': 'tai-nghe', 'description': 'Tai nghe Bluetooth', 'parent': 'phu-kien'},
    ]

    for cat in category_data:
        if not Category.objects.filter(slug=cat['slug']).exists():
            category = Category.objects.create(
                name=cat['name'],
                slug=cat['slug'],
                description=cat['description'],
                is_active=True
            )
            print(f"   ✅ Created category: {category.name}")

    # Create products
    parent_categories = Category.objects.filter(parent__isnull=True)
    all_categories = Category.objects.all()

    product_templates = [
        {'name': 'iPhone 15 Pro Max', 'category': 'iphone', 'price': 34990000, 'desc': 'iPhone 15 Pro Max 256GB'},
        {'name': 'Samsung Galaxy S24 Ultra', 'category': 'samsung', 'price': 28990000, 'desc': 'Galaxy S24 Ultra 512GB'},
        {'name': 'MacBook Pro 14" M3 Pro', 'category': 'macbook', 'price': 39990000, 'desc': 'MacBook Pro 14" M3 Pro 512GB'},
        {'name': 'Dell XPS 13 Plus', 'category': 'dell', 'price': 32990000, 'desc': 'Dell XPS 13 Plus Core i7'},
        {'name': 'iPad Pro 11 M2', 'category': 'ipad', 'price': 23990000, 'desc': 'iPad Pro 11 inch M2 128GB'},
        {'name': 'Samsung Galaxy Tab S9', 'category': 'samsung-tablet', 'price': 19990000, 'desc': 'Galaxy Tab S9 5G'},
        {'name': 'AirPods Pro 2', 'category': 'tai-nghe', 'price': 6190000, 'desc': 'Apple AirPods Pro 2 Type-C'},
        {'name': 'Sony WH-1000XM5', 'category': 'tai-nghe', 'price': 7990000, 'desc': 'Tai nghe chụp tai chống ồn Sony WH-1000XM5'},
        {'name': 'iPhone 13', 'category': 'iphone', 'price': 15990000, 'desc': 'iPhone 13 128GB'},
        {'name': 'Dell Inspiron 15', 'category': 'dell', 'price': 16990000, 'desc': 'Dell Inspiron 15 Core i5'},
    ]


    for i, template in enumerate(product_templates):
        # We need a proper sequence independent of category for slugs uniqueness if we change the loop below
        category = Category.objects.get(slug=template['category'])
        product_slug = f"{template['category']}-{i}"
        if not Product.objects.filter(slug=product_slug).exists():
            product = Product.objects.create(
                sku=f"SKU-{template['category'].upper()}-{i+1:03d}",
                name=template['name'],
                slug=product_slug,
                description=template['desc'],
                category=category,
                base_price=template['price'],
                compare_price=int(template['price'] * 1.1),
                images=[f"https://via.placeholder.com/400x400?text={template['name'].replace(' ', '+')}"],
                tags=['hot', 'new'],
                is_active=True
            )
            print(f"   ✅ Created product: {product.name} ({product.base_price:,.0f} VNĐ)")

    print("   ✅ Product database populated successfully!\n")

def populate_cart_db():
    """Populate cart database with sample carts"""
    print("🛒 Populating Cart database...")
    if os.path.exists('services/cart'):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'services.cart.config.settings')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    django.setup()

    from apps.cart.models import Cart, CartItem

    # Get sample users and products
    user_ids = [str(uuid.uuid4()) for _ in range(5)]

    for i, user_id in enumerate(user_ids):
        cart, created = Cart.objects.get_or_create(
            user_id=user_id,
            defaults={'session_id': str(uuid.uuid4())}
        )
        if created:
            # Add random items to cart
            num_items = random.randint(1, 3)
            for j in range(num_items):
                product_id = str(uuid.uuid4())
                CartItem.objects.create(
                    cart=cart,
                    product_id=product_id,
                    quantity=random.randint(1, 5),
                    price=random.randint(100000, 50000000)
                )
            print(f"   ✅ Created cart with {num_items} items for user {i+1}")

    print("   ✅ Cart database populated successfully!\n")

def populate_order_db():
    """Populate order database with sample orders"""
    print("📦 Populating Order database...")
    if os.path.exists('services/order'):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'services.order.config.settings')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    django.setup()

    from apps.order.models import Order, OrderItem

    user_ids = [str(uuid.uuid4()) for _ in range(5)]
    statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']

    for i, user_id in enumerate(user_ids):
        order = Order.objects.create(
            order_id=f"ORD{datetime.now().strftime('%Y%m%d')}{i+1:04d}",
            user_id=user_id,
            status=random.choice(statuses),
            total_amount=random.randint(500000, 50000000),
            currency='VND',
            shipping_address={
                'street': f'{random.randint(1, 500)} Đường Example',
                'city': 'Hà Nội',
                'country': 'Vietnam',
                'postal_code': str(random.randint(100000, 999999))
            }
        )

        # Add items to order
        num_items = random.randint(1, 5)
        for j in range(num_items):
            OrderItem.objects.create(
                order=order,
                product_id=str(uuid.uuid4()),
                product_name=f"Product {j+1}",
                quantity=random.randint(1, 3),
                price=random.randint(100000, 10000000),
                subtotal=random.randint(100000, 30000000)
            )

        print(f"   ✅ Created order: {order.order_id} ({order.status})")

    print("   ✅ Order database populated successfully!\n")

def populate_review_db():
    """Populate review database with sample reviews"""
    print("⭐ Populating Review database...")
    if os.path.exists('services/review'):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'services.review.config.settings')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    django.setup()

    from apps.review.models import Review

    product_ids = [str(uuid.uuid4()) for _ in range(10)]
    user_ids = [str(uuid.uuid4()) for _ in range(15)]

    review_templates = [
        "Sản phẩm tuyệt vời! Rất hài lòng.",
        "Chất lượng tốt, giao hàng nhanh.",
        "Giá cả hợp lý, sẽ mua lại.",
        "Đáng tiền, đề xuất cho mọi người.",
        "Sản phẩm OK, không có gì để phàn nàn.",
        "Dịch vụ khách hàng tốt.",
        "Giao hàng nhanh, đóng gói cẩn thận.",
    ]

    for i in range(30):
        Review.objects.create(
            product_id=random.choice(product_ids),
            user_id=random.choice(user_ids),
            user_name=f"User {random.randint(1, 100)}",
            rating=random.randint(3, 5),
            title=random.choice(["Tốt", "Rất tốt", "Xuất sắc", "Hài lòng"]),
            body=random.choice(review_templates),
            is_verified_purchase=random.choice([True, False]),
            is_approved=True,
            helpful_count=random.randint(0, 50)
        )

    print(f"   ✅ Created 30 sample reviews")
    print("   ✅ Review database populated successfully!\n")

def populate_ai_db():
    """Populate AI database with additional knowledge and FAQs"""
    print("🤖 Populating AI database...")
    if os.path.exists('services/ai'):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'services.ai.config.settings')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    django.setup()

    from apps.knowledge_base.models import FAQCategory, FAQ, KnowledgeDocument
    from apps.chatbot.models import SystemPrompt

    # Create additional FAQ categories and FAQs
    additional_faqs = [
        {
            'category': 'orders',
            'question': 'Làm sao để hủy đơn hàng?',
            'answer': 'Bạn có thể hủy đơn hàng trong vòng 30 phút sau khi đặt hàng. Vui lòng liên hệ tổng đài 1900 xxxx để được hỗ trợ.',
            'priority': 9,
            'keywords': ['hủy', 'huỷ', 'cancel', 'đơn hàng']
        },
        {
            'category': 'orders',
            'question': 'Thời gian giao hàng bao lâu?',
            'answer': 'Thời gian giao hàng thường từ 2-7 ngày làm việc tùy theo khu vực. Hà Nội và TP.HCM: 2-3 ngày, các tỉnh khác: 3-7 ngày.',
            'priority': 10,
            'keywords': ['thời gian', 'giao hàng', 'ship', 'vận chuyển']
        },
        {
            'category': 'returns',
            'question': 'Tôi có thể đổi trả sản phẩm không?',
            'answer': 'Có, bạn có thể đổi trả sản phẩm trong vòng 30 ngày kể từ ngày mua. Sản phẩm phải còn nguyên bao bì và không có dấu hiệu sử dụng.',
            'priority': 10,
            'keywords': ['đổi', 'trả', 'return', 'exchange']
        },
        {
            'category': 'payments',
            'question': 'Các phương thức thanh toán nào được chấp nhận?',
            'answer': 'Chúng tôi chấp nhận thanh toán tiền mặt khi nhận hàng, thẻ tín dụng/ghi nợ, ví điện tử (Momo, ZaloPay, ShopeePay) và chuyển khoản ngân hàng.',
            'priority': 10,
            'keywords': ['thanh toán', 'payment', 'tiền', 'thẻ', 'ví']
        },
    ]

    for faq_data in additional_faqs:
        category = FAQCategory.objects.get(slug=faq_data['category'])
        faq, created = FAQ.objects.get_or_create(
            question=faq_data['question'],
            defaults={
                'category': category,
                'answer': faq_data['answer'],
                'priority': faq_data['priority'],
                'keywords': faq_data['keywords']
            }
        )
        if created:
            print(f"   ✅ Created FAQ: {faq.question[:50]}...")

    # Create knowledge documents
    doc_templates = [
        {
            'doc_type': 'policy',
            'title': 'Chính sách bảo mật thông tin',
            'content': 'Chúng tôi cam kết bảo mật thông tin cá nhân của khách hàng... Thông tin bao gồm: tên, địa chỉ, số điện thoại, email, thông tin thanh toán... Thông tin sẽ được sử dụng cho mục đích xử lý đơn hàng và cải thiện dịch vụ...',
            'language': 'vi'
        },
        {
            'doc_type': 'policy',
            'title': 'Chính sách vận chuyển',
            'content': 'Chúng tôi cung cấp các phương thức vận chuyển: Standard (5-7 ngày), Express (2-3 ngày), Next Day (ngày hôm sau). Phí vận chuyển miễn cho đơn hàng trên 500K...',
            'language': 'vi'
        },
        {
            'doc_type': 'guide',
            'title': 'Hướng dẫn đặt hàng online',
            'content': 'Bước 1: Chọn sản phẩm và thêm vào giỏ hàng. Bước 2: Nhập thông tin giao hàng. Bước 3: Chọn phương thức thanh toán. Bước 4: Xác nhận đơn hàng...',
            'language': 'vi'
        },
    ]

    for doc_data in doc_templates:
        doc, created = KnowledgeDocument.objects.get_or_create(
            title=doc_data['title'],
            defaults={
                'doc_id': f"doc_{uuid.uuid4().hex[:8]}",
                'doc_type': doc_data['doc_type'],
                'content': doc_data['content'],
                'language': doc_data['language'],
                'is_active': True
            }
        )
        if created:
            print(f"   ✅ Created document: {doc.title}")

    print("   ✅ AI database populated successfully!\n")

def main():
    """Main function to populate all databases"""
    print("🚀 Starting database population for all services...\n")

    import subprocess
    import traceback
    
    # If the script is called with an argument, it means we are in the worker process
    if len(sys.argv) > 1 and sys.argv[1] == '--worker':
        worker_func = sys.argv[2]
        try:
            globals()[worker_func]()
        except Exception as e:
            print(f"❌ Error in {worker_func}: {str(e)}")
            traceback.print_exc()
            sys.exit(1)
        sys.exit(0)

    try:
        # Run each populator in a separate process to avoid Django AppRegistry conflict
        populators = [
            'populate_auth_db',
            'populate_product_db',
            'populate_cart_db',
            'populate_order_db',
            'populate_review_db',
            'populate_ai_db',
        ]
        
        for func in populators:
            res = subprocess.run([sys.executable, __file__, '--worker', func], check=False)
            if res.returncode != 0:
                print(f"❌ Population stopped due to error in {func}")
                return

        print("🎉 All databases populated successfully!")
        print("\n📝 Summary:")
        print("   ✅ Auth: Users, Admin accounts")
        print("   ✅ Product: Categories, Products, Attributes")
        print("   ✅ Cart: Shopping carts with items")
        print("   ✅ Order: Orders with various statuses")
        print("   ✅ Review: Product reviews and ratings")
        print("   ✅ AI: Knowledge base, FAQs, System prompts")
        print("\n🔐 Login credentials:")
        print("   Admin: admin / admin123")
        print("   Users: user1-user10 / password123")

    except Exception as e:
        print(f"❌ Error during population: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--worker':
        pass # Handle in main
    main()
