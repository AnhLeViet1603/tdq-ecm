#!/bin/bash
# Auto-initialization script for AI Service
set -e

echo "🤖 AI Service - Auto-initialization"

if [ -f "/app/.initialized" ]; then
    echo "✅ Already initialized"
    exit 0
fi

echo "⏳ Waiting for database..."
while ! python manage.py shell -c "from django.db import connection; connection.ensure_connection()" 2>/dev/null; do
    sleep 2
done

python manage.py shell << 'EOF'
from apps.knowledge_base.models import FAQCategory, FAQ, KnowledgeDocument
from apps.chatbot.models import SystemPrompt
import uuid

print("📚 Creating FAQ categories and FAQs...")

# Create FAQ categories if they don't exist
categories_data = [
    {'name': 'Products', 'slug': 'products', 'description': 'Product-related questions'},
    {'name': 'Orders', 'slug': 'orders', 'description': 'Order and shipping questions'},
    {'name': 'Returns', 'slug': 'returns', 'description': 'Return and refund questions'},
    {'name': 'Account', 'slug': 'account', 'description': 'Account management questions'},
]

for cat_data in categories_data:
    category, created = FAQCategory.objects.get_or_create(
        slug=cat_data['slug'],
        defaults={
            'name': cat_data['name'],
            'description': cat_data['description']
        }
    )
    if created:
        print(f"  ✅ Created category: {category.name}")

# Create FAQs
faqs_data = [
    {
        'category': 'orders',
        'question': 'What are your shipping options?',
        'answer': 'We offer Standard (5-7 days), Express (2-3 days), and Next Day delivery. Free shipping for orders over 500K VND.',
        'priority': 10,
        'keywords': ['shipping', 'delivery', 'options']
    },
    {
        'category': 'returns',
        'question': 'What is your return policy?',
        'answer': 'We accept returns within 30 days of purchase. Items must be unused and in original packaging.',
        'priority': 10,
        'keywords': ['return', 'refund', 'policy', 'exchange']
    },
    {
        'category': 'products',
        'question': 'How do I find the right product?',
        'answer': 'Use our search function, browse categories, or try our AI-powered recommendations.',
        'priority': 8,
        'keywords': ['find', 'search', 'product', 'recommendation']
    },
]

for faq_data in faqs_data:
    try:
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
            print(f"  ✅ Created FAQ: {faq.question[:50]}...")
    except Exception as e:
        print(f"  ⚠️ FAQ creation error: {e}")

# Create default system prompt
if not SystemPrompt.objects.filter(name='default_ecommerce_assistant').exists():
    prompt_text = '''You are a helpful e-commerce assistant for an online store.
Your role is to assist customers with:
- Product information and recommendations
- Order inquiries and support
- Shipping and delivery questions
- Return and refund policies
- General shopping assistance
Use the provided context to give accurate, helpful responses.
If the context doesn't contain relevant information, be honest and suggest contacting customer support.
Always be friendly, professional, and concise.'''

    SystemPrompt.objects.create(
        name='default_ecommerce_assistant',
        description='Default e-commerce assistant prompt',
        prompt_template=prompt_text,
        variables=['context', 'language'],
        temperature=0.7,
        max_tokens=1000,
        is_active=True,
        version=1
    )
    print("  ✅ Created default system prompt")

print("✅ AI service initialized!")
EOF

touch /app/.initialized
