from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ConversationViewSet, ChatbotView, FeedbackView,
    SystemPromptViewSet, ChatbotAnalyticsViewSet
)

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'system-prompts', SystemPromptViewSet, basename='system-prompt')
router.register(r'analytics', ChatbotAnalyticsViewSet, basename='chatbot-analytics')

urlpatterns = [
    path('', include(router.urls)),
    path('chat/', ChatbotView.as_view(), name='chat'),
    path('feedback/', FeedbackView.as_view(), name='feedback'),
]
