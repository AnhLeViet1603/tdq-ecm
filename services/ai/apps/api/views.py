"""
views.py – AI Service API endpoints
=====================================
Endpoints:
  POST /api/chatbot/chat/          – RAG chat tư vấn
  GET  /api/recommendations/       – Gợi ý sản phẩm theo hành vi
  GET  /api/behavior-insight/      – Phân tích ý định người dùng
  POST /api/behavior-train/        – Kick off training vòng lặp DL
  GET  /api/kb/faq-categories/     – Danh mục FAQ
  GET  /api/kb/faq/                – FAQ theo category_id
  POST /api/kb/search/             – Tìm kiếm trong Knowledge Base
  POST /api/kb/add-document/       – Thêm tài liệu mới vào KB
  POST /api/graph/update/          – Cập nhật đồ thị hành vi
  GET  /api/graph/user/            – Graph quan hệ của người dùng
"""

import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services.rag_chatbot import RAGChatbot
from .services.behavior_model import UserBehaviorModel
from .services.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton instances (shared across requests)
# ---------------------------------------------------------------------------
chatbot        = RAGChatbot()
behavior_model = UserBehaviorModel()
kb             = chatbot.kb     # Share the same KB instance


# ===========================================================================
# 1. RAG Chat
# ===========================================================================
class ChatbotAPIView(APIView):
    """
    POST /api/chatbot/chat/
    Body:
      {
        "message":        "Làm sao đổi trả hàng?",
        "session_id":     "sess_abc123",        (optional)
        "user_id":        "user_42",            (optional)
        "event_sequence": ["search","click"],   (optional)
        "use_rag":        true,                 (optional, default true)
        "top_k":          3                     (optional, default 3)
      }
    """

    def post(self, request):
        message = request.data.get("message", "").strip()
        if not message:
            return Response(
                {"error": "Trường 'message' là bắt buộc."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = chatbot.chat(
            user_message=message,
            session_id=request.data.get("session_id", "default"),
            user_id=request.data.get("user_id", "guest"),
            event_sequence=request.data.get("event_sequence", []),
            top_k=int(request.data.get("top_k", 3)),
            use_rag=request.data.get("use_rag", True),
        )
        return Response(result, status=status.HTTP_200_OK)

    def delete(self, request):
        """DELETE /api/chatbot/chat/?session_id=xxx – Xoá session."""
        session_id = request.query_params.get("session_id", "default")
        chatbot.clear_session(session_id)
        return Response({"message": f"Session '{session_id}' đã được xoá."})


# ===========================================================================
# 2. Recommendations
# ===========================================================================
class RecommendationAPIView(APIView):
    """
    GET /api/recommendations/?user_id=xxx&limit=5
    Kết hợp:
      - UserBehaviorModel → intent prediction
      - KnowledgeBase graph → top interest products
    """

    def get(self, request):
        user_id = request.query_params.get("user_id", "guest")
        limit   = min(int(request.query_params.get("limit", 10)), 50)

        # Lấy sản phẩm có interest cao nhất từ graph
        top_products = kb.get_top_interest_products(user_id, top_k=limit)

        # Phân tích intent theo event sequence giả lập
        # (Production: fetch from interaction-service)
        dummy_events = ["search", "view", "click", "add_to_cart"]
        behavior     = behavior_model.predict_intent(dummy_events)

        # Build mock recommendations (production: query product-service)
        mock_recs = []
        for i, prod_id in enumerate(top_products[:limit], 1):
            mock_recs.append({
                "id":    prod_id,
                "rank":  i,
                "score": kb.user_interest.get(user_id, {}).get(prod_id, 0.0),
            })

        # Nếu chưa có graph data, trả về mock list
        if not mock_recs:
            mock_recs = [
                {"id": "prod-1", "name": "Sản phẩm gợi ý 1", "price": 100_000},
                {"id": "prod-2", "name": "Sản phẩm gợi ý 2", "price": 200_000},
                {"id": "prod-3", "name": "Sản phẩm gợi ý 3", "price": 300_000},
            ][:limit]

        return Response({
            "user_id":          user_id,
            "recommendations":  mock_recs,
            "behavior_insight": behavior,
        })


# ===========================================================================
# 3. Behavior Insight (Deep Learning)
# ===========================================================================
class BehaviorInsightAPIView(APIView):
    """
    GET /api/behavior-insight/?user_id=xxx
    Query Params:
      events – Comma-separated event names, e.g. "search,click,add_to_cart"
    """

    def get(self, request):
        user_id    = request.query_params.get("user_id", "guest")
        events_str = request.query_params.get("events", "")
        events     = [e.strip() for e in events_str.split(",") if e.strip()] if events_str else []

        result = behavior_model.predict_intent(events)
        return Response({
            "user_id":    user_id,
            "events":     events,
            "prediction": result,
        })


class BehaviorTrainAPIView(APIView):
    """
    POST /api/behavior-train/
    Body: { "epochs": 10, "lr": 0.001 }
    Kick off model training (cold-start or retrain).
    """

    def post(self, request):
        epochs = int(request.data.get("epochs", 10))
        lr     = float(request.data.get("lr", 1e-3))
        try:
            history = behavior_model.train(epochs=epochs, lr=lr)
            return Response({
                "status":  "Training hoàn tất.",
                "history": history,
            })
        except Exception as exc:
            logger.error(f"Training failed: {exc}")
            return Response(
                {"error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ===========================================================================
# 4. Knowledge Base
# ===========================================================================
class FAQCategoriesAPIView(APIView):
    """GET /api/kb/faq-categories/ – Danh mục FAQ."""

    def get(self, request):
        return Response({"data": kb.get_faq_categories()})


class FAQListAPIView(APIView):
    """GET /api/kb/faq/?category_id=1 – FAQ theo category."""

    def get(self, request):
        category_id = int(request.query_params.get("category_id", 0))
        if category_id:
            data = kb.get_faq_by_category(category_id)
        else:
            data = [
                {"id": d.id, "category": d.category, "question": d.question, "answer": d.answer}
                for d in kb.documents
            ]
        return Response({"data": data, "total": len(data)})


class KBSearchAPIView(APIView):
    """
    POST /api/kb/search/
    Body: { "query": "...", "top_k": 3 }
    """

    def post(self, request):
        query = request.data.get("query", "").strip()
        if not query:
            return Response({"error": "'query' là bắt buộc."}, status=400)
        top_k   = int(request.data.get("top_k", 3))
        results = kb.search(query, top_k=top_k)
        return Response({"query": query, "results": results, "total": len(results)})


class KBAddDocumentAPIView(APIView):
    """
    POST /api/kb/add-document/
    Body: { "id": "doc_x", "category": "faq", "question": "...", "answer": "...", "keywords": [...] }
    """

    def post(self, request):
        required = ["id", "category", "question", "answer"]
        missing  = [f for f in required if not request.data.get(f)]
        if missing:
            return Response(
                {"error": f"Thiếu trường: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        chatbot.add_knowledge(request.data)
        return Response({"message": f"Tài liệu '{request.data['id']}' đã được thêm vào KB."})


# ===========================================================================
# 5. Graph Operations
# ===========================================================================
class GraphUpdateAPIView(APIView):
    """
    POST /api/graph/update/
    Body: { "user_id": "123", "product_id": "456", "event": "click", "category_id": "10" }
    """

    def post(self, request):
        required = ["user_id", "product_id", "event"]
        missing  = [f for f in required if not request.data.get(f)]
        if missing:
            return Response({"error": f"Thiếu trường: {', '.join(missing)}"}, status=400)

        chatbot.update_user_graph(
            user_id=request.data["user_id"],
            product_id=request.data["product_id"],
            event=request.data["event"],
            category_id=request.data.get("category_id", ""),
        )
        return Response({"message": "Graph đã được cập nhật."})


class GraphUserAPIView(APIView):
    """GET /api/graph/user/?user_id=xxx – Lấy đồ thị quan hệ của user."""

    def get(self, request):
        user_id = request.query_params.get("user_id", "guest")
        graph   = chatbot.get_user_graph(user_id)
        return Response(graph)
