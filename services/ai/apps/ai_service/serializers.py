from rest_framework import serializers
from .models import UserBehavior, RecommendationModel, ProductEmbedding, RecommendationCache


class UserBehaviorSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBehavior
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'timestamp']


class RecommendationModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationModel
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_trained_at']


class ProductEmbeddingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductEmbedding
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class RecommendationCacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationCache
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'generated_at']


class RecommendationRequestSerializer(serializers.Serializer):
    """Request serializer for recommendations"""
    user_id = serializers.UUIDField(required=True)
    product_id = serializers.UUIDField(required=False)
    category_id = serializers.UUIDField(required=False)
    algorithm = serializers.CharField(default='neural_cf', required=False)
    limit = serializers.IntegerField(default=10, min_value=1, max_value=50)
    exclude_purchased = serializers.BooleanField(default=False)


class RecommendationResponseSerializer(serializers.Serializer):
    """Response serializer for recommendations"""
    product_id = serializers.UUIDField()
    product_name = serializers.CharField()
    score = serializers.FloatField()
    reason = serializers.CharField(required=False)
    metadata = serializers.DictField(required=False)


class TrainingRequestSerializer(serializers.Serializer):
    """Request serializer for model training"""
    model_type = serializers.ChoiceField(
        choices=['collaborative_filtering', 'content_based', 'neural_cf', 'hybrid']
    )
    hyperparameters = serializers.DictField(required=False)
    min_interactions = serializers.IntegerField(default=5)
