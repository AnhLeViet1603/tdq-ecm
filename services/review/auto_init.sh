#!/usr/bin/env python
import os
import sys
import django
import random
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/app')
django.setup()

from apps.review.models import Review, ReviewMedia


def create_sample_reviews():
    """Create sample reviews for testing"""

    # Sample user IDs (should match auth service users)
    users = [
        {'id': '11111111-1111-1111-1111-111111111111', 'name': 'Nguyễn Văn An'},
        {'id': '22222222-2222-2222-2222-222222222222', 'name': 'Trần Thị Bình'},
        {'id': '33333333-3333-3333-3333-333333333333', 'name': 'Lê Văn Cường'},
        {'id': '44444444-4444-4444-4444-444444444444', 'name': 'Phạm Thị Dung'},
        {'id': '55555555-5555-5555-5555-555555555555', 'name': 'Hoàng Văn Em'},
    ]

    # Sample product IDs (should match product service products)
    products = [
        '00000000-0000-0000-0000-000000000001',  # iPhone 15 Pro Max
        '00000000-0000-0000-0000-000000000002',  # MacBook Air M2
        '00000000-0000-0000-0000-000000000003',  # AirPods Pro 2
        '00000000-0000-0000-0000-000000000004',  # Samsung Galaxy S24 Ultra
        '00000000-0000-0000-0000-000000000005',  # iPad Air 5
        '00000000-0000-0000-0000-000000000006',  # Sony WH-1000XM5
        '00000000-0000-0000-0000-000000000007',  # Dell XPS 15
        '00000000-0000-0000-0000-000000000008',  # Nintendo Switch OLED
    ]

    # Review templates
    review_templates = [
        {
            'title': 'Sản phẩm tuyệt vời',
            'body': 'Chất lượng sản phẩm rất tốt, giao hàng nhanh. Đóng gói cẩn thận, đúng mô tả. Sẽ ủng hộ shop thêm!',
            'rating': 5
        },
        {
            'title': 'Hài lòng với sản phẩm',
            'body': 'Sản phẩm dùng ổn định, giá cả hợp lý. Màu sắc đẹp, thiết kế hiện đại. Có thể cân nhắc mua thêm.',
            'rating': 4
        },
        {
            'title': 'Rất tốt',
            'body': 'Mua về dùng được 1 tuần rồi, rất hài lòng. Pin trâu, hiệu năng mạnh. Recommend cho mọi người!',
            'rating': 5
        },
        {
            'title': 'Ổng nhưng chưa hoàn hảo',
            'body': 'Sản phẩm tốt nhưng có một chút nhỏ nhặt. Tổng kết vẫn đáng tiền. Shop tư vấn nhiệt tình.',
            'rating': 4
        },
        {
            'title': 'Đáng tiền',
            'body': 'Giá cả cạnh hợp, chất lượng tốt hơn mong đợi. Đóng gói kỹ càng, giao hàng đúng hẹn.',
            'rating': 4
        },
        {
            'title': 'Siêu phẩm',
            'body': 'Xứng đáng 5 sao! Từ chất lượng đến dịch vụ đều tuyệt vời. Sẽ quay lại mua lần sau.',
            'rating': 5
        },
        {
            'title': 'Chưa thực sự hài lòng',
            'body': 'Sản phẩm dùng được nhưng chưa thực sự xuất sắc. Có thể cân nhắc改进 một số điểm.',
            'rating': 3
        },
        {
            'title': 'Tạm được',
            'body': 'Phù hợp với giá tiền. Dùng cơ bản thì ổn, không đòi hỏi cao.',
            'rating': 3
        }
    ]

    seller_replies = [
        'Cảm ơn khách hàng đã đánh giá! Shop rất vui khi bạn hài lòng với sản phẩm.',
        'Cảm ơn feedback của bạn. Shop sẽ cố gắng cải thiện thêm trong thời gian tới.',
        'Cảm ơn bạn đã ủng hộ shop! Chúc bạn sử dụng sản phẩm vui vẻ.',
        'Xin lỗi vì bất tiện này. Shop sẽ liên hệ với bạn để hỗ trợ tốt nhất.',
        'Cảm ơn đánh giá chi tiết của bạn. Hy vọng sẽ được phục vụ bạn thêm nhiều lần nữa.'
    ]

    reviews_created = 0

    for product_id in products:
        # Create 3-8 reviews per product
        num_reviews = random.randint(3, 8)

        for i in range(num_reviews):
            user = random.choice(users)
            template = random.choice(review_templates)

            # Check if this user already reviewed this product (avoid duplicates)
            existing_review = Review.objects.filter(
                product_id=product_id,
                user_id=user['id']
            ).first()

            if existing_review:
                continue

            # Random date within last 60 days
            review_date = datetime.now() - timedelta(days=random.randint(1, 60))

            # Create review
            review = Review.objects.create(
                product_id=product_id,
                user_id=user['id'],
                user_name=user['name'],
                rating=template['rating'],
                title=template['title'],
                body=template['body'],
                is_verified_purchase=random.choice([True, False]),
                is_approved=True,
                helpful_count=random.randint(0, 15),
                reply=random.choice([''] + seller_replies) if random.random() > 0.6 else '',
                replied_at=review_date + timedelta(days=random.randint(1, 7)) if random.random() > 0.7 else None,
                created_at=review_date
            )

            # Maybe add some media
            if random.random() > 0.7:  # 30% chance to add media
                num_media = random.randint(1, 3)
                for j in range(num_media):
                    ReviewMedia.objects.create(
                        review=review,
                        media_type=random.choice(['image', 'video']),
                        url=f'https://example.com/reviews/{review.id}_{j}.jpg',
                        thumbnail_url=f'https://example.com/reviews/thumbs/{review.id}_{j}.jpg',
                        sort_order=j
                    )

            reviews_created += 1
            print(f"✓ Created review for product {product_id[-8:]} by {user['name']} ({template['rating']}★)")

    print(f"\n✅ Created {reviews_created} sample reviews")


if __name__ == '__main__':
    print("🌱 Starting review data initialization...")
    create_sample_reviews()
    print("🎉 Review initialization completed!")
