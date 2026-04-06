from django.contrib import admin
from .models import (
    Conversation, Message, ConversationContext, ChatbotAnalytics,
    IntentPrediction, SystemPrompt
)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['conversation_id', 'user_id', 'title', 'status', 'language', 'started_at', 'ended_at']
    list_filter = ['status', 'language', 'started_at', 'ended_at']
    search_fields = ['conversation_id', 'user_id', 'session_id', 'title']
    readonly_fields = ['created_at', 'updated_at', 'started_at', 'ended_at']
    date_hierarchy = 'started_at'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['message_id', 'conversation', 'role', 'feedback', 'used_rag', 'confidence_score', 'timestamp']
    list_filter = ['role', 'used_rag', 'timestamp', 'created_at']
    search_fields = ['message_id', 'content', 'conversation__conversation_id']
    readonly_fields = ['created_at', 'updated_at', 'timestamp']
    date_hierarchy = 'timestamp'


@admin.register(ConversationContext)
class ConversationContextAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'context_type', 'expires_at', 'created_at']
    list_filter = ['context_type', 'expires_at', 'created_at']
    search_fields = ['conversation__conversation_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ChatbotAnalytics)
class ChatbotAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_conversations', 'total_messages', 'avg_conversation_length',
                    'satisfaction_score', 'resolution_rate', 'rag_usage_count']
    list_filter = ['date']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'


@admin.register(IntentPrediction)
class IntentPredictionAdmin(admin.ModelAdmin):
    list_display = ['message', 'intent', 'confidence', 'is_correct', 'created_at']
    list_filter = ['intent', 'is_correct', 'created_at']
    search_fields = ['message__content', 'intent']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SystemPrompt)
class SystemPromptAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'temperature', 'max_tokens', 'version']
    list_filter = ['is_active', 'version', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Prompt Configuration', {
            'fields': ('prompt_template', 'variables', 'temperature', 'max_tokens')
        }),
        ('Version Control', {
            'fields': ('version',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
