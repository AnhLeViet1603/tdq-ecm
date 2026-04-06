from rest_framework import serializers
from .models import (
    Conversation, Message, ConversationContext, ChatbotAnalytics,
    IntentPrediction, SystemPrompt
)


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'started_at']


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'timestamp']


class ConversationContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationContext
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChatbotAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatbotAnalytics
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class IntentPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntentPrediction
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class SystemPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemPrompt
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChatRequestSerializer(serializers.Serializer):
    """Request serializer for chat messages"""
    message = serializers.CharField(required=True, max_length=5000)
    conversation_id = serializers.UUIDField(required=False)
    user_id = serializers.UUIDField(required=False)
    session_id = serializers.UUIDField(required=False)
    language = serializers.CharField(default='en', required=False)
    use_rag = serializers.BooleanField(default=True)
    context = serializers.DictField(required=False)


class ChatResponseSerializer(serializers.Serializer):
    """Response serializer for chat messages"""
    conversation_id = serializers.UUIDField()
    message_id = serializers.UUIDField()
    role = serializers.CharField()
    content = serializers.CharField()
    retrieved_docs = serializers.ListField(required=False)
    confidence_score = serializers.FloatField(required=False)
    used_rag = serializers.BooleanField(required=False)
    suggestions = serializers.ListField(required=False)


class FeedbackRequestSerializer(serializers.Serializer):
    """Request serializer for message feedback"""
    message_id = serializers.UUIDField(required=True)
    feedback = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True)
