from django.db import models
from shared.base_model import BaseModel


class KnowledgeDocument(BaseModel):
    """Store knowledge base documents"""
    DOC_TYPES = [
        ('product', 'Product Information'),
        ('faq', 'FAQ'),
        ('policy', 'Policy'),
        ('guide', 'User Guide'),
        ('troubleshooting', 'Troubleshooting'),
    ]

    doc_id = models.CharField(max_length=255, unique=True, db_index=True)
    doc_type = models.CharField(max_length=50, choices=DOC_TYPES)
    title = models.CharField(max_length=500)
    content = models.TextField()
    summary = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    source = models.CharField(max_length=255, blank=True)  # URL, file path, etc.
    language = models.CharField(max_length=10, default='en')
    is_active = models.BooleanField(default=True)
    vector_id = models.CharField(max_length=255, blank=True)  # ID in vector database

    # Vector embeddings
    embedding = models.JSONField(null=True, blank=True)
    embedding_model = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'knowledge_documents'
        indexes = [
            models.Index(fields=['doc_type', 'is_active']),
            models.Index(fields=['language']),
        ]


class FAQCategory(BaseModel):
    """FAQ categories for better organization"""
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=300, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'faq_categories'
        ordering = ['sort_order', 'name']


class FAQ(BaseModel):
    """Frequently Asked Questions"""
    category = models.ForeignKey(FAQCategory, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=500)
    answer = models.TextField()
    keywords = models.JSONField(default=list)  # Keywords for matching
    priority = models.IntegerField(default=0)  # Higher priority shown first
    views_count = models.IntegerField(default=0)
    helpful_count = models.IntegerField(default=0)
    not_helpful_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    related_products = models.JSONField(default=list)  # Related product IDs

    class Meta:
        db_table = 'faqs'
        ordering = ['-priority', '-created_at']


class ProductKnowledge(BaseModel):
    """Product-specific knowledge and expert information"""
    product_id = models.UUIDField(db_index=True)
    product_name = models.CharField(max_length=500)
    expert_tips = models.TextField(blank=True)
    common_issues = models.JSONField(default=list)
    usage_guide = models.TextField(blank=True)
    specifications = models.JSONField(default=dict)
    compatibility_info = models.TextField(blank=True)
    maintenance_tips = models.TextField(blank=True)
    video_tutorials = models.JSONField(default=list)  # List of video URLs
    related_docs = models.JSONField(default=list)  # Related knowledge doc IDs

    class Meta:
        db_table = 'product_knowledge'
        indexes = [
            models.Index(fields=['product_id']),
        ]


class VectorIndex(BaseModel):
    """Track vector database indices and their status"""
    index_name = models.CharField(max_length=255, unique=True)
    index_type = models.CharField(max_length=100)  # faiss, chroma, pinecone
    dimension = models.IntegerField()
    metadata = models.JSONField(default=dict)
    document_count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'vector_indices'
