from django.urls import path
from .views import (
    ChatbotAPIView,
    RecommendationAPIView,
    BehaviorInsightAPIView,
    BehaviorTrainAPIView,
    FAQCategoriesAPIView,
    FAQListAPIView,
    KBSearchAPIView,
    KBAddDocumentAPIView,
    GraphUpdateAPIView,
    GraphUserAPIView,
)

urlpatterns = [
    # ── RAG Chatbot ───────────────────────────────────────────────────────
    path("chatbot/chat/",           ChatbotAPIView.as_view(),         name="chatbot_chat"),

    # ── Recommendations ───────────────────────────────────────────────────
    path("recommendations/",        RecommendationAPIView.as_view(),  name="recommendations"),

    # ── Behavior Analysis (Deep Learning) ─────────────────────────────────
    path("behavior-insight/",       BehaviorInsightAPIView.as_view(), name="behavior_insight"),
    path("behavior-train/",         BehaviorTrainAPIView.as_view(),   name="behavior_train"),

    # ── Knowledge Base ────────────────────────────────────────────────────
    path("kb/faq-categories/",      FAQCategoriesAPIView.as_view(),   name="faq_categories"),
    path("kb/faq/",                 FAQListAPIView.as_view(),         name="faq_list"),
    path("kb/search/",              KBSearchAPIView.as_view(),        name="kb_search"),
    path("kb/add-document/",        KBAddDocumentAPIView.as_view(),   name="kb_add_document"),

    # ── Graph Operations ──────────────────────────────────────────────────
    path("graph/update/",           GraphUpdateAPIView.as_view(),     name="graph_update"),
    path("graph/user/",             GraphUserAPIView.as_view(),       name="graph_user"),
]
