#!/bin/bash

# AI Service Setup Script
# This script helps initialize the AI service with sample data and configuration

set -e

echo "================================"
echo "AI Service Setup Script"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_message $YELLOW "Creating .env file from .env.example..."
    cp .env.example .env
    print_message $GREEN ".env file created. Please update it with your configuration."
    print_message $YELLOW "In particular, set your OPENAI_API_KEY if you want to use LLM features."
    echo ""
fi

# Check if directories exist
print_message $YELLOW "Checking required directories..."
mkdir -p ml_models
mkdir -p vector_db
print_message $GREEN "Directories created/verified."

# Wait for database
print_message $YELLOW "Waiting for database connection..."
while ! pg_isready -h ${DB_HOST:-postgres} -p ${DB_PORT:-5432} -U ${DB_USER:-postgres} 2>/dev/null; do
    echo "Database is unavailable - waiting..."
    sleep 2
done
print_message $GREEN "Database is ready!"

# Run migrations
print_message $YELLOW "Running database migrations..."
python manage.py migrate --noinput
print_message $GREEN "Migrations completed."

# Create sample data
print_message $YELLOW "Creating sample knowledge base data..."

# Create FAQ categories
python manage.py shell << 'EOF'
from apps.knowledge_base.models import FAQCategory, FAQ

# Create FAQ categories
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
        print(f"Created FAQ category: {category.name}")

# Create sample FAQs
products_cat = FAQCategory.objects.get(slug='products')
orders_cat = FAQCategory.objects.get(slug='orders')
returns_cat = FAQCategory.objects.get(slug='returns')

faqs_data = [
    {
        'category': products_cat,
        'question': 'How do I find the right product for me?',
        'answer': 'You can browse our categories, use the search function, or try our AI-powered recommendation system. For personalized recommendations, tell us about your preferences and needs.',
        'priority': 10,
        'keywords': ['find', 'search', 'product', 'recommendation']
    },
    {
        'category': orders_cat,
        'question': 'What are your shipping options?',
        'answer': 'We offer Standard shipping (5-7 business days), Express shipping (2-3 business days), and Next Day delivery. Shipping is free for orders over $50.',
        'priority': 10,
        'keywords': ['shipping', 'delivery', 'options', 'timeline']
    },
    {
        'category': orders_cat,
        'question': 'How can I track my order?',
        'answer': 'Once your order ships, you will receive a tracking number via email. You can also track your order in your account dashboard or contact customer support.',
        'priority': 8,
        'keywords': ['track', 'order', 'status', 'tracking number']
    },
    {
        'category': returns_cat,
        'question': 'What is your return policy?',
        'answer': 'We accept returns within 30 days of purchase. Items must be unused and in original packaging. Contact our support team to initiate a return.',
        'priority': 10,
        'keywords': ['return', 'refund', 'policy', 'exchange']
    },
]

for faq_data in faqs_data:
    faq, created = FAQ.objects.get_or_create(
        question=faq_data['question'],
        defaults=faq_data
    )
    if created:
        print(f"Created FAQ: {faq.question}")

print("Sample FAQs created successfully!")
EOF

print_message $GREEN "Sample data created."

# Create system prompts
print_message $YELLOW "Creating system prompts..."
python manage.py shell << 'EOF'
from apps.chatbot.models import SystemPrompt

# Create default system prompt
default_prompt, created = SystemPrompt.objects.get_or_create(
    name='default_ecommerce_assistant',
    defaults={
        'description': 'Default e-commerce assistant prompt',
        'prompt_template': '''You are a helpful e-commerce assistant for an online store.
Your role is to assist customers with:
- Product information and recommendations
- Order inquiries and support
- Shipping and delivery questions
- Return and refund policies
- General shopping assistance

Use the provided context to give accurate, helpful responses.
If the context doesn't contain relevant information, be honest and suggest contacting customer support.
Always be friendly, professional, and concise.''',
        'variables': ['context', 'language'],
        'temperature': 0.7,
        'max_tokens': 1000,
        'is_active': True,
        'version': 1
    }
)

if created:
    print("Default system prompt created.")
else:
    print("Default system prompt already exists.")
EOF

print_message $GREEN "System prompts created."

# Create superuser if requested
echo ""
read -p "Do you want to create a superuser? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_message $YELLOW "Creating superuser..."
    python manage.py createsuperuser
fi

# Final message
print_message $GREEN "================================"
print_message $GREEN "AI Service setup completed!"
print_message $GREEN "================================"
echo ""
print_message $YELLOW "Next steps:"
echo "1. Update your .env file with your configuration"
echo "2. Set your OPENAI_API_KEY for LLM features"
echo "3. Start the service: python manage.py runserver 0.0.0.0:8010"
echo "4. Access admin panel: http://localhost:8010/admin/"
echo "5. Upload knowledge documents via admin panel or API"
echo "6. Train recommendation models with your data"
echo ""
print_message $YELLOW "API Documentation available at:"
echo "http://localhost:8010/api/v1/"
echo ""
