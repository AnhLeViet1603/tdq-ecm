from django.db import models
from shared.base_model import BaseModel


class Conversation(BaseModel):
    """Chat conversation session"""
    conversation_id = models.UUIDField(unique=True, db_index=True)
    user_id = models.UUIDField(db_index=True, null=True, blank=True)  # Anonymous if null
    session_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=50, default='active')  # active, archived, deleted
    language = models.CharField(max_length=10, default='en')
    metadata = models.JSONField(default=dict)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'conversations'
        indexes = [
            models.Index(fields=['user_id', 'created_at']),
            models.Index(fields=['session_id', 'created_at']),
        ]


class Message(BaseModel):
    """Individual messages in a conversation"""
    ROLE_TYPES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    message_id = models.UUIDField(unique=True, db_index=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_TYPES)
    content = models.TextField()
    metadata = models.JSONField(default=dict)

    # RAG-related fields
    retrieved_docs = models.JSONField(default=list)  # Retrieved document IDs
    confidence_score = models.FloatField(null=True, blank=True)
    used_rag = models.BooleanField(default=False)

    # Feedback
    feedback = models.IntegerField(null=True, blank=True)  # 1-5 rating
    feedback_comment = models.TextField(blank=True)

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'messages'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
        ]


class ConversationContext(BaseModel):
    """Store context information for conversations"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='contexts')
    context_type = models.CharField(max_length=100)  # product_viewing, cart_context, search_context
    context_data = models.JSONField(default=dict)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'conversation_contexts'
        indexes = [
            models.Index(fields=['conversation', 'context_type']),
            models.Index(fields=['expires_at']),
        ]


class ChatbotAnalytics(BaseModel):
    """Track chatbot performance and analytics"""
    date = models.DateField(db_index=True)
    total_conversations = models.IntegerField(default=0)
    total_messages = models.IntegerField(default=0)
    avg_conversation_length = models.FloatField(default=0)
    avg_response_time = models.FloatField(default=0)  # seconds
    satisfaction_score = models.FloatField(null=True, blank=True)
    resolution_rate = models.FloatField(default=0)
    rag_usage_count = models.IntegerField(default=0)
    top_intents = models.JSONField(default=list)  # Most common conversation intents
    language_distribution = models.JSONField(default=dict)

    class Meta:
        db_table = 'chatbot_analytics'
        unique_together = ['date']
        ordering = ['-date']


class IntentPrediction(BaseModel):
    """Store intent predictions for message classification"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='intents')
    intent = models.CharField(max_length=100)
    confidence = models.FloatField()
    entities = models.JSONField(default=dict)  # Extracted entities
    is_correct = models.BooleanField(null=True, blank=True)  # Human feedback

    class Meta:
        db_table = 'intent_predictions'


class SystemPrompt(BaseModel):
    """Manage system prompts for different scenarios"""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    prompt_template = models.TextField()
    variables = models.JSONField(default=list)  # Required template variables
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=1000)
    is_active = models.BooleanField(default=True)
    version = models.IntegerField(default=1)

    class Meta:
        db_table = 'system_prompts'
        ordering = ['-version']
