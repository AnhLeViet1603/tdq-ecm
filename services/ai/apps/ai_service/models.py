from django.db import models
from shared.base_model import BaseModel


class UserBehavior(BaseModel):
    """Track user behavior for recommendation model training"""
    user_id = models.UUIDField(db_index=True)
    session_id = models.UUIDField(db_index=True, null=True, blank=True)
    action_type = models.CharField(max_length=50)  # view, click, add_to_cart, purchase, search
    product_id = models.UUIDField(db_index=True, null=True, blank=True)
    category_id = models.UUIDField(db_index=True, null=True, blank=True)
    search_query = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)  # Additional context
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'user_behaviors'
        indexes = [
            models.Index(fields=['user_id', 'timestamp']),
            models.Index(fields=['action_type', 'timestamp']),
        ]


class RecommendationModel(BaseModel):
    """Store ML model metadata and performance metrics"""
    model_name = models.CharField(max_length=255, unique=True)
    model_type = models.CharField(max_length=100)  # collaborative_filtering, content_based, neural_cf
    version = models.CharField(max_length=50)
    is_active = models.BooleanField(default=False)
    model_path = models.TextField()
    accuracy = models.FloatField(null=True, blank=True)
    precision = models.FloatField(null=True, blank=True)
    recall = models.FloatField(null=True, blank=True)
    f1_score = models.FloatField(null=True, blank=True)
    training_samples = models.IntegerField(default=0)
    last_trained_at = models.DateTimeField(null=True, blank=True)
    hyperparameters = models.JSONField(default=dict)

    class Meta:
        db_table = 'recommendation_models'
        ordering = ['-created_at']


class ProductEmbedding(BaseModel):
    """Store product embeddings for similarity search"""
    product_id = models.UUIDField(unique=True, db_index=True)
    embedding = models.JSONField()  # Store as JSON array
    embedding_model = models.CharField(max_length=255)
    vector_dimension = models.IntegerField()
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = 'product_embeddings'
        indexes = [
            models.Index(fields=['product_id']),
        ]


class RecommendationCache(BaseModel):
    """Cache recommendations to improve performance"""
    user_id = models.UUIDField(db_index=True)
    recommendations = models.JSONField()
    algorithm_used = models.CharField(max_length=100)
    generated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    hit_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'recommendation_cache'
        indexes = [
            models.Index(fields=['user_id', 'expires_at']),
        ]
