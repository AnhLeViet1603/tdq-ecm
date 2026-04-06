from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
import uuid

from .models import (
    KnowledgeDocument, FAQCategory, FAQ, ProductKnowledge, VectorIndex
)
from .serializers import (
    KnowledgeDocumentSerializer, FAQCategorySerializer, FAQSerializer,
    ProductKnowledgeSerializer, VectorIndexSerializer,
    DocumentSearchRequestSerializer, DocumentUploadSerializer
)
# from ml_models.rag_pipeline import RAGEngine, ProductKnowledgeExtractor  # Disabled - too heavy


class KnowledgeDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for KnowledgeDocument model"""
    queryset = KnowledgeDocument.objects.all()
    serializer_class = KnowledgeDocumentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        doc_type = self.request.query_params.get('doc_type')
        is_active = self.request.query_params.get('is_active', 'true').lower() == 'true'

        if doc_type:
            queryset = queryset.filter(doc_type=doc_type)
        if is_active:
            queryset = queryset.filter(is_active=True)

        return queryset

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload and index a new document (Simplified - no ML)"""
        serializer = DocumentUploadSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Create document without heavy ML indexing
                doc = KnowledgeDocument.objects.create(
                    doc_id=f"doc_{uuid.uuid4().hex}",
                    doc_type=serializer.validated_data['doc_type'],
                    title=serializer.validated_data['title'],
                    content=serializer.validated_data['content'],
                    summary=serializer.validated_data.get('summary', ''),
                    metadata=serializer.validated_data.get('metadata', {}),
                    source=serializer.validated_data.get('source', ''),
                    language=serializer.validated_data.get('language', 'en')
                )

                # Skip ML indexing for now - too heavy
                doc.vector_id = doc.doc_id
                doc.save()

                return Response({
                    'status': 'success',
                    'document_id': doc.doc_id,
                    'message': 'Document uploaded successfully (ML indexing disabled for performance)'
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({
                    'status': 'error',
                    'message': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def search(self, request):
        """Search for relevant documents (Simplified - no ML)"""
        serializer = DocumentSearchRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                query = serializer.validated_data['query']
                top_k = serializer.validated_data.get('top_k', 5)

                # Simple text search without ML - much faster
                documents = KnowledgeDocument.objects.filter(
                    title__icontains=query
                ) | KnowledgeDocument.objects.filter(
                    content__icontains=query
                )

                results = []
                for doc in documents[:top_k]:
                    results.append({
                        'document_id': doc.doc_id,
                        'content': doc.content[:500] + '...' if len(doc.content) > 500 else doc.content,
                        'metadata': doc.metadata,
                        'similarity_score': 0.8  # Mock score
                    })

                return Response({
                    'status': 'success',
                    'query': query,
                    'results': results,
                    'count': len(results),
                    'note': 'Using simple text search (ML disabled for performance)'
                })

            except Exception as e:
                return Response({
                    'status': 'error',
                    'message': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def reindex(self, request, pk=None):
        """Re-index a document (Simplified - no ML)"""
        try:
            doc = self.get_object()

            # Skip ML reindexing - too heavy
            return Response({
                'status': 'success',
                'message': f'Document {doc.doc_id} updated successfully (ML reindexing disabled for performance)'
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FAQCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for FAQCategory model"""
    queryset = FAQCategory.objects.filter(is_active=True)
    serializer_class = FAQCategorySerializer


class FAQViewSet(viewsets.ModelViewSet):
    """ViewSet for FAQ model"""
    queryset = FAQ.objects.filter(is_active=True)
    serializer_class = FAQSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.query_params.get('category_id')

        if category_id:
            queryset = queryset.filter(category_id=category_id)

        return queryset

    @action(detail=True, methods=['post'])
    def mark_helpful(self, request, pk=None):
        """Mark FAQ as helpful"""
        try:
            faq = self.get_object()
            faq.helpful_count += 1
            faq.save()

            return Response({
                'status': 'success',
                'helpful_count': faq.helpful_count
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def mark_not_helpful(self, request, pk=None):
        """Mark FAQ as not helpful"""
        try:
            faq = self.get_object()
            faq.not_helpful_count += 1
            faq.save()

            return Response({
                'status': 'success',
                'not_helpful_count': faq.not_helpful_count
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search FAQs by keyword"""
        keyword = request.query_params.get('keyword', '')

        if not keyword:
            return Response({
                'status': 'error',
                'message': 'Keyword parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Search in question and answer
        faqs = FAQ.objects.filter(
            is_active=True,
            question__icontains=keyword
        ) | FAQ.objects.filter(
            is_active=True,
            answer__icontains=keyword
        )

        serializer = self.get_serializer(faqs, many=True)
        return Response({
            'status': 'success',
            'results': serializer.data,
            'count': len(serializer.data)
        })


class ProductKnowledgeViewSet(viewsets.ModelViewSet):
    """ViewSet for ProductKnowledge model"""
    queryset = ProductKnowledge.objects.all()
    serializer_class = ProductKnowledgeSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        product_id = self.request.query_params.get('product_id')

        if product_id:
            queryset = queryset.filter(product_id=product_id)

        return queryset

    @action(detail=False, methods=['post'])
    def index_product(self, request):
        """Index product knowledge (Simplified - no ML)"""
        try:
            product_id = request.data.get('product_id')
            if not product_id:
                return Response({
                    'status': 'error',
                    'message': 'product_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get or create product knowledge without ML indexing
            product_knowledge, created = ProductKnowledge.objects.get_or_create(
                product_id=product_id,
                defaults={
                    'product_name': request.data.get('product_name', 'Unknown Product'),
                    'expert_tips': request.data.get('expert_tips', ''),
                    'common_issues': request.data.get('common_issues', []),
                    'usage_guide': request.data.get('usage_guide', ''),
                    'specifications': request.data.get('specifications', {}),
                    'compatibility_info': request.data.get('compatibility_info', ''),
                    'maintenance_tips': request.data.get('maintenance_tips', ''),
                }
            )

            # Skip ML indexing - too heavy
            return Response({
                'status': 'success',
                'message': f'Product knowledge saved successfully (ML indexing disabled for performance)',
                'product_id': str(product_id)
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VectorIndexViewSet(viewsets.ModelViewSet):
    """ViewSet for VectorIndex model"""
    queryset = VectorIndex.objects.all()
    serializer_class = VectorIndexSerializer

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get vector database statistics (Simplified - no ML)"""
        try:
            # Return mock stats instead of querying ML database
            stats = {
                'total_documents': KnowledgeDocument.objects.count(),
                'total_faq': FAQ.objects.count(),
                'total_product_knowledge': ProductKnowledge.objects.count(),
                'note': 'ML vector database disabled for performance'
            }

            return Response({
                'status': 'success',
                'stats': stats
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
