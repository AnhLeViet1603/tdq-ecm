from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    KnowledgeDocumentViewSet, FAQCategoryViewSet, FAQViewSet,
    ProductKnowledgeViewSet, VectorIndexViewSet
)

router = DefaultRouter()
router.register(r'documents', KnowledgeDocumentViewSet, basename='knowledge-document')
router.register(r'faq-categories', FAQCategoryViewSet, basename='faq-category')
router.register(r'faqs', FAQViewSet, basename='faq')
router.register(r'product-knowledge', ProductKnowledgeViewSet, basename='product-knowledge')
router.register(r'vector-indices', VectorIndexViewSet, basename='vector-index')

urlpatterns = [
    path('', include(router.urls)),
]
