from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid
# import numpy as np  # Disabled - too heavy

from .models import UserBehavior, RecommendationModel, ProductEmbedding, RecommendationCache
from .serializers import (
    UserBehaviorSerializer, RecommendationModelSerializer,
    ProductEmbeddingSerializer, RecommendationCacheSerializer,
    RecommendationRequestSerializer, RecommendationResponseSerializer,
    TrainingRequestSerializer
)
# from ml_models.recommender import NeuralCollaborativeFiltering, HybridRecommender  # Disabled - too heavy


class UserBehaviorViewSet(viewsets.ModelViewSet):
    """ViewSet for UserBehavior model"""
    queryset = UserBehavior.objects.all()
    serializer_class = UserBehaviorSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset


class RecommendationModelViewSet(viewsets.ModelViewSet):
    """ViewSet for RecommendationModel management"""
    queryset = RecommendationModel.objects.all()
    serializer_class = RecommendationModelSerializer

    @action(detail=False, methods=['post'])
    def train(self, request):
        """Train a new recommendation model (Simplified - no ML)"""
        serializer = TrainingRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Skip heavy ML training - create mock model instead
                model_record = RecommendationModel.objects.create(
                    model_name=f"Simple Model {uuid.uuid4().hex[:8]}",
                    model_type=serializer.validated_data['model_type'],
                    version="1.0",
                    is_active=True,
                    model_path="mock_path",  # No actual model saved
                    hyperparameters=serializer.validated_data.get('hyperparameters', {}),
                    accuracy=0.85,  # Mock accuracy
                    last_trained_at=timezone.now()
                )

                return Response({
                    'status': 'success',
                    'model_id': model_record.id,
                    'message': 'Model created successfully (ML training disabled for performance)'
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({
                    'status': 'error',
                    'message': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a specific model"""
        try:
            model = self.get_object()
            # Deactivate all other models of the same type
            RecommendationModel.objects.filter(
                model_type=model.model_type,
                is_active=True
            ).update(is_active=False)

            # Activate this model
            model.is_active = True
            model.save()

            return Response({'status': 'success', 'message': f'Model {model.model_name} activated'})

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RecommendationView(APIView):
    """API endpoint for getting recommendations"""

    def post(self, request):
        """Get product recommendations for a user (Simplified - no ML)"""
        serializer = RecommendationRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user_id = serializer.validated_data['user_id']
                limit = serializer.validated_data.get('limit', 10)

                # Return mock recommendations instead of heavy ML computation
                recommendations = [
                    {
                        'product_id': '00000000-0000-0000-0000-000000000001',
                        'product_name': 'iPhone 15 Pro Max',
                        'score': 0.95,
                        'reason': 'Popular product matching your preferences',
                        'price': 32990000,
                        'image': 'https://picsum.photos/seed/iphone/200/200.jpg'
                    },
                    {
                        'product_id': '00000000-0000-0000-0000-000000000002',
                        'product_name': 'MacBook Air M2',
                        'score': 0.88,
                        'reason': 'Based on your browsing history',
                        'price': 26990000,
                        'image': 'https://picsum.photos/seed/macbook/200/200.jpg'
                    },
                    {
                        'product_id': '00000000-0000-0000-0000-000000000003',
                        'product_name': 'AirPods Pro 2',
                        'score': 0.82,
                        'reason': 'Frequently bought together',
                        'price': 5990000,
                        'image': 'https://picsum.photos/seed/airpods/200/200.jpg'
                    }
                ]

                return Response({
                    'source': 'mock',
                    'recommendations': recommendations[:limit],
                    'note': 'Using mock recommendations (ML disabled for performance)'
                })

            except Exception as e:
                return Response({
                    'status': 'error',
                    'message': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _get_recommendations(self, user_id, algorithm, limit, context):
        """Get recommendations using specified algorithm"""
        # This is a placeholder implementation
        # In production, this would use the actual trained models

        if algorithm == 'collaborative_filtering':
            return self._collaborative_filtering_rec(user_id, limit)
        elif algorithm == 'content_based':
            return self._content_based_rec(user_id, limit, context)
        elif algorithm == 'neural_cf':
            return self._neural_cf_rec(user_id, limit)
        else:
            return self._hybrid_rec(user_id, limit, context)

    def _collaborative_filtering_rec(self, user_id, limit):
        """Collaborative filtering recommendations"""
        # Placeholder - implement based on your user-item interaction matrix
        return [
            {
                'product_id': str(uuid.uuid4()),
                'score': 0.95,
                'reason': 'Users with similar preferences also liked this'
            }
        ]

    def _content_based_rec(self, user_id, limit, context):
        """Content-based recommendations"""
        # Placeholder - implement based on item features and user history
        return []

    def _neural_cf_rec(self, user_id, limit):
        """Neural collaborative filtering recommendations"""
        # Load the active NCF model and generate recommendations
        active_model = RecommendationModel.objects.filter(
            model_type='neural_cf',
            is_active=True
        ).first()

        if not active_model:
            return self._collaborative_filtering_rec(user_id, limit)

        # Load model and generate recommendations
        # ncf_model = NeuralCollaborativeFiltering(...)
        # recommendations = ncf_model.predict(user_id, ...)
        return []

    def _hybrid_rec(self, user_id, limit, context):
        """Hybrid recommendations combining multiple approaches"""
        # Combine results from multiple algorithms
        cf_recs = self._collaborative_filtering_rec(user_id, limit // 2)
        cb_recs = self._content_based_rec(user_id, limit // 2, context)

        # Merge and score
        combined = {}
        for rec in cf_recs:
            product_id = rec['product_id']
            combined[product_id] = combined.get(product_id, 0) + rec['score'] * 0.6

        for rec in cb_recs:
            product_id = rec['product_id']
            combined[product_id] = combined.get(product_id, 0) + rec['score'] * 0.4

        # Sort and return
        sorted_recs = sorted(combined.items(), key=lambda x: x[1], reverse=True)
        return [
            {'product_id': pid, 'score': score, 'reason': 'Hybrid recommendation'}
            for pid, score in sorted_recs[:limit]
        ]


class ProductEmbeddingViewSet(viewsets.ModelViewSet):
    """ViewSet for ProductEmbedding model"""
    queryset = ProductEmbedding.objects.all()
    serializer_class = ProductEmbeddingSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        product_id = self.request.query_params.get('product_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset

    @action(detail=False, methods=['post'])
    def generate_batch(self, request):
        """Generate embeddings for multiple products (Simplified - no ML)"""
        try:
            # Skip heavy sentence transformers - create mock embeddings
            product_ids = request.data.get('product_ids', [])
            if not product_ids:
                return Response({
                    'status': 'error',
                    'message': 'No product IDs provided'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create mock embeddings without heavy ML models
            embeddings_created = []
            for product_id in product_ids:
                # Create simple hash-based embedding instead of ML
                import hashlib
                hash_obj = hashlib.md5(str(product_id).encode())
                embedding = [float(ord(c)) / 255.0 for c in hash_obj.hexdigest()[:64]]

                obj, created = ProductEmbedding.objects.update_or_create(
                    product_id=product_id,
                    defaults={
                        'embedding': embedding,
                        'embedding_model': 'simple_hash',
                        'vector_dimension': len(embedding)
                    }
                )
                embeddings_created.append(str(product_id))

            return Response({
                'status': 'success',
                'embeddings_created': embeddings_created,
                'count': len(embeddings_created),
                'note': 'Using simple hash embeddings (ML disabled for performance)'
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TrackBehaviorView(APIView):
    """API endpoint for tracking user behavior"""

    def post(self, request):
        """Track user behavior for recommendation training"""
        try:
            behavior_data = request.data.copy()
            behavior_data['user_id'] = behavior_data.get('user_id', str(uuid.uuid4()))

            serializer = UserBehaviorSerializer(data=behavior_data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status': 'success',
                    'message': 'Behavior tracked successfully'
                }, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
