from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserBehaviorViewSet, RecommendationModelViewSet,
    ProductEmbeddingViewSet, RecommendationView, TrackBehaviorView
)

router = DefaultRouter()
router.register(r'behaviors', UserBehaviorViewSet, basename='user-behavior')
router.register(r'models', RecommendationModelViewSet, basename='recommendation-model')
router.register(r'embeddings', ProductEmbeddingViewSet, basename='product-embedding')

urlpatterns = [
    path('', include(router.urls)),
    path('recommendations/', RecommendationView.as_view(), name='recommendations'),
    path('track-behavior/', TrackBehaviorView.as_view(), name='track-behavior'),
]
