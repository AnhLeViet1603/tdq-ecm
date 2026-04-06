from rest_framework import serializers
from .models import (
    KnowledgeDocument, FAQCategory, FAQ, ProductKnowledge, VectorIndex
)


class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeDocument
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'vector_id']


class FAQCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQCategory
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class FAQSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = FAQ
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductKnowledgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductKnowledge
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class VectorIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = VectorIndex
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_updated']


class DocumentSearchRequestSerializer(serializers.Serializer):
    """Request serializer for document search"""
    query = serializers.CharField(required=True)
    doc_type = serializers.CharField(required=False)
    top_k = serializers.IntegerField(default=5, min_value=1, max_value=20)
    min_similarity = serializers.FloatField(default=0.6, min_value=0.0, max_value=1.0)
    language = serializers.CharField(default='en', required=False)


class DocumentUploadSerializer(serializers.Serializer):
    """Request serializer for document upload"""
    doc_type = serializers.ChoiceField(choices=KnowledgeDocument.DOC_TYPES)
    title = serializers.CharField(max_length=500)
    content = serializers.CharField(required=True)
    summary = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.DictField(required=False)
    source = serializers.CharField(required=False, allow_blank=True)
    language = serializers.CharField(default='en', required=False)
