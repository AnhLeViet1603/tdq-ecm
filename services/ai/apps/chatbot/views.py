from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db import models
from datetime import timedelta
import uuid
import json

from .models import (
    Conversation, Message, ConversationContext, ChatbotAnalytics,
    IntentPrediction, SystemPrompt
)
from .serializers import (
    ConversationSerializer, MessageSerializer, ConversationContextSerializer,
    ChatbotAnalyticsSerializer, IntentPredictionSerializer, SystemPromptSerializer,
    ChatRequestSerializer, ChatResponseSerializer, FeedbackRequestSerializer
)
from ml_models.rag_pipeline import RAGEngine, ConversationManager


class ConversationViewSet(viewsets.ModelViewSet):
    """ViewSet for Conversation model"""
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get('user_id')
        session_id = self.request.query_params.get('session_id')

        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if session_id:
            queryset = queryset.filter(session_id=session_id)

        return queryset.order_by('-created_at')

    @action(detail=False, methods=['post'])
    def start(self, request):
        """Start a new conversation"""
        try:
            user_id = request.data.get('user_id')
            session_id = request.data.get('session_id', str(uuid.uuid4()))
            title = request.data.get('title', '')
            language = request.data.get('language', 'en')

            # Create conversation
            conversation = Conversation.objects.create(
                conversation_id=uuid.uuid4(),
                user_id=user_id,
                session_id=session_id,
                title=title,
                language=language,
                status='active'
            )

            serializer = self.get_serializer(conversation)
            return Response({
                'status': 'success',
                'conversation': serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """End a conversation"""
        try:
            conversation = self.get_object()
            conversation.status = 'archived'
            conversation.ended_at = timezone.now()
            conversation.save()

            return Response({
                'status': 'success',
                'message': 'Conversation ended successfully'
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get conversation history"""
        try:
            conversation = self.get_object()
            messages = conversation.messages.all().order_by('timestamp')

            serializer = MessageSerializer(messages, many=True)
            return Response({
                'status': 'success',
                'messages': serializer.data,
                'conversation_id': str(conversation.conversation_id)
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatbotView(APIView):
    """Main chatbot API endpoint for handling conversations"""

    def post(self, request):
        """Process a chat message and generate response"""
        serializer = ChatRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user_message = serializer.validated_data['message']
                conversation_id = serializer.validated_data.get('conversation_id')
                user_id = serializer.validated_data.get('user_id')
                session_id = serializer.validated_data.get('session_id', str(uuid.uuid4()))
                language = serializer.validated_data.get('language', 'en')
                use_rag = serializer.validated_data.get('use_rag', True)
                context = serializer.validated_data.get('context', {})

                # Get or create conversation
                if conversation_id:
                    conversation = Conversation.objects.filter(conversation_id=conversation_id).first()
                    if not conversation:
                        return Response({
                            'status': 'error',
                            'message': 'Conversation not found'
                        }, status=status.HTTP_404_NOT_FOUND)
                else:
                    conversation = Conversation.objects.create(
                        conversation_id=uuid.uuid4(),
                        user_id=user_id,
                        session_id=session_id,
                        language=language,
                        status='active'
                    )

                # Create user message
                user_msg = Message.objects.create(
                    message_id=uuid.uuid4(),
                    conversation=conversation,
                    role='user',
                    content=user_message
                )

                # Generate bot response
                bot_response_data = self._generate_response(
                    conversation, user_message, use_rag, context
                )

                # Create bot message
                bot_msg = Message.objects.create(
                    message_id=uuid.uuid4(),
                    conversation=conversation,
                    role='assistant',
                    content=bot_response_data['response'],
                    retrieved_docs=bot_response_data.get('retrieved_docs', []),
                    confidence_score=bot_response_data.get('confidence_score'),
                    used_rag=bot_response_data.get('used_rag', False)
                )

                # Update analytics
                self._update_analytics(conversation, use_rag)

                # Format response
                response_serializer = ChatResponseSerializer({
                    'conversation_id': conversation.conversation_id,
                    'message_id': bot_msg.message_id,
                    'role': 'assistant',
                    'content': bot_msg.content,
                    'retrieved_docs': bot_msg.retrieved_docs,
                    'confidence_score': bot_msg.confidence_score,
                    'used_rag': bot_msg.used_rag,
                    'suggestions': bot_response_data.get('suggestions', [])
                })

                return Response(response_serializer.data)

            except Exception as e:
                return Response({
                    'status': 'error',
                    'message': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _generate_response(self, conversation, user_message, use_rag, context):
        """Generate bot response using RAG or fallback"""
        rag_engine = RAGEngine()
        conv_manager = ConversationManager(rag_engine)

        # Add user message to conversation history
        conv_manager.add_message(
            str(conversation.conversation_id),
            'user',
            user_message
        )

        retrieved_docs = []
        confidence_score = None
        used_rag = False

        if use_rag:
            # Generate contextual query
            contextual_query = conv_manager.generate_contextual_query(
                str(conversation.conversation_id),
                user_message
            )

            # Retrieve relevant documents
            retrieved_docs = rag_engine.retrieve_documents(
                query=contextual_query,
                top_k=5,
                min_similarity=0.6
            )

            if retrieved_docs:
                used_rag = True
                confidence_score = retrieved_docs[0]['similarity']

        # Generate response
        if use_rag and retrieved_docs:
            response = rag_engine.generate_response(
                query=user_message,
                retrieved_docs=retrieved_docs,
                context={'language': conversation.language}
            )
        else:
            # Fallback response
            response = self._generate_fallback_response(user_message, conversation)

        # Add bot response to conversation history
        conv_manager.add_message(
            str(conversation.conversation_id),
            'assistant',
            response
        )

        # Generate suggestions
        suggestions = self._generate_suggestions(user_message, retrieved_docs)

        return {
            'response': response,
            'retrieved_docs': [doc['id'] for doc in retrieved_docs],
            'confidence_score': confidence_score,
            'used_rag': used_rag,
            'suggestions': suggestions
        }

    def _generate_fallback_response(self, user_message, conversation):
        """Generate fallback response without RAG"""
        # Simple rule-based responses for common queries
        user_lower = user_message.lower()

        if any(word in user_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            return f"Hello! How can I help you today?"

        elif any(word in user_lower for word in ['order', 'status', 'track']):
            return "I can help you check your order status. Could you please provide your order number?"

        elif any(word in user_lower for word in ['return', 'refund', 'exchange']):
            return "I'd be happy to help you with returns or refunds. Our policy allows returns within 30 days of purchase. Would you like specific details about the return process?"

        elif any(word in user_lower for word in ['shipping', 'delivery', 'ship']):
            return "We offer several shipping options: Standard (5-7 business days), Express (2-3 business days), and Next Day delivery. Shipping is free for orders over $50. How can I help you with shipping?"

        elif any(word in user_lower for word in ['product', 'item', 'recommend', 'suggest']):
            return "I can help you find products! Could you tell me more about what you're looking for? For example, the type of product, your budget, or any specific features you need?"

        elif any(word in user_lower for word in ['thank', 'thanks']):
            return "You're welcome! Is there anything else I can help you with?"

        else:
            return "I understand you're looking for help. Could you please provide more details about what you need assistance with? I'm here to help with product information, orders, shipping, returns, and more."

    def _generate_suggestions(self, user_message, retrieved_docs):
        """Generate follow-up suggestions based on context"""
        suggestions = []

        # Extract product categories from retrieved docs
        if retrieved_docs:
            for doc in retrieved_docs[:3]:
                metadata = doc.get('metadata', {})
                if 'doc_type' in metadata:
                    if metadata['doc_type'] == 'product':
                        suggestions.append("Tell me more about this product")
                    elif metadata['doc_type'] == 'faq':
                        suggestions.append("Show me related FAQs")

        # Add general suggestions
        if len(suggestions) < 3:
            general_suggestions = [
                "Check my order status",
                "Browse products",
                "Contact customer support",
                "View return policy"
            ]
            suggestions.extend(general_suggestions[:3 - len(suggestions)])

        return suggestions[:3]

    def _update_analytics(self, conversation, used_rag):
        """Update chatbot analytics"""
        today = timezone.now().date()
        analytics, created = ChatbotAnalytics.objects.get_or_create(
            date=today,
            defaults={
                'total_conversations': 0,
                'total_messages': 0,
                'rag_usage_count': 0
            }
        )

        analytics.total_messages += 2  # User + bot message
        if used_rag:
            analytics.rag_usage_count += 1

        # Check if this is a new conversation today
        if conversation.created_at.date() == today:
            new_conversation = not ChatbotAnalytics.objects.filter(
                date=today,
                total_conversations__gte=1
            ).exists()
            if new_conversation:
                analytics.total_conversations += 1

        analytics.save()


class FeedbackView(APIView):
    """API endpoint for message feedback"""

    def post(self, request):
        """Submit feedback for a message"""
        serializer = FeedbackRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                message_id = serializer.validated_data['message_id']
                feedback = serializer.validated_data['feedback']
                comment = serializer.validated_data.get('comment', '')

                # Update message with feedback
                message = Message.objects.filter(message_id=message_id).first()
                if not message:
                    return Response({
                        'status': 'error',
                        'message': 'Message not found'
                    }, status=status.HTTP_404_NOT_FOUND)

                message.feedback = feedback
                message.feedback_comment = comment
                message.save()

                return Response({
                    'status': 'success',
                    'message': 'Feedback submitted successfully'
                })

            except Exception as e:
                return Response({
                    'status': 'error',
                    'message': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SystemPromptViewSet(viewsets.ModelViewSet):
    """ViewSet for SystemPrompt management"""
    queryset = SystemPrompt.objects.filter(is_active=True)
    serializer_class = SystemPromptSerializer

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a system prompt"""
        try:
            prompt = self.get_object()
            return Response({
                'status': 'success',
                'prompt': prompt.prompt_template,
                'variables': prompt.variables
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatbotAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ChatbotAnalytics (read-only)"""
    queryset = ChatbotAnalytics.objects.all()
    serializer_class = ChatbotAnalyticsSerializer

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get analytics summary for the last 30 days"""
        try:
            thirty_days_ago = timezone.now().date() - timedelta(days=30)
            recent_analytics = ChatbotAnalytics.objects.filter(
                date__gte=thirty_days_ago
            ).order_by('-date')

            # Calculate summary
            total_conversations = sum(a.total_conversations for a in recent_analytics)
            total_messages = sum(a.total_messages for a in recent_analytics)
            total_rag_usage = sum(a.rag_usage_count for a in recent_analytics)

            avg_satisfaction = recent_analytics.filter(
                satisfaction_score__isnull=False
            ).aggregate(avg=models.Avg('satisfaction_score'))['avg__avg'] or 0

            summary = {
                'period_days': 30,
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'total_rag_usage': total_rag_usage,
                'average_satisfaction_score': avg_satisfaction,
                'rag_usage_rate': total_rag_usage / total_messages if total_messages > 0 else 0
            }

            return Response({
                'status': 'success',
                'summary': summary
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
