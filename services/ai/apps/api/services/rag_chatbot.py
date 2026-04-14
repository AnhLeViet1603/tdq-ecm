"""
rag_chatbot.py
==============
RAG (Retrieval-Augmented Generation) Chatbot cho hệ thống tư vấn E-Commerce.

Pipeline:
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ User Query                                                               │
  │    ↓                                                                     │
  │ [1] Retrieve  – Tìm context từ KnowledgeBase (FAISS semantic search)    │
  │    ↓                                                                     │
  │ [2] Augment   – Xây dựng prompt: System + Context + History + Query     │
  │    ↓                                                                     │
  │ [3] Generate  – Gọi LLM (gemini-1.5-flash / mock LLM)                  │
  │    ↓                                                                     │
  │ Response + Citations                                                     │
  └─────────────────────────────────────────────────────────────────────────┘

Hỗ trợ:
  - Session history (đa lượt hội thoại)
  - Behavior-aware context (tích hợp BehaviorModel)
  - Citation tracing (trả về nguồn tài liệu đã dùng)
  - Fallback rule-based khi LLM không khả dụng
"""

import os
import logging
import datetime
from dataclasses import dataclass, field

from .knowledge_base import KnowledgeBase
from .behavior_model import UserBehaviorModel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional: Google Generative AI (Gemini) integration
# ---------------------------------------------------------------------------
try:
    import google.generativeai as genai

    _GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    if _GEMINI_API_KEY:
        genai.configure(api_key=_GEMINI_API_KEY)
        _GEMINI_MODEL = genai.GenerativeModel("gemini-1.5-flash")
        _GEMINI_AVAILABLE = True
        logger.info("Gemini LLM available and configured.")
    else:
        _GEMINI_AVAILABLE = False
        logger.info("GEMINI_API_KEY not set – using rule-based fallback.")
except ImportError:
    _GEMINI_AVAILABLE = False
    logger.info("google-generativeai not installed – using rule-based fallback.")


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------
@dataclass
class ChatMessage:
    role: str     # "user" | "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())


@dataclass
class ChatSession:
    session_id: str
    user_id: str
    history: list[ChatMessage] = field(default_factory=list)
    max_history: int = 10       # Số lượt hội thoại lưu tối đa

    def add(self, role: str, content: str):
        self.history.append(ChatMessage(role=role, content=content))
        # Giới hạn lịch sử
        if len(self.history) > self.max_history * 2:
            self.history = self.history[-self.max_history * 2:]

    def format_history(self) -> str:
        if not self.history:
            return ""
        lines = []
        for msg in self.history[-6:]:   # Chỉ dùng 6 lượt gần nhất
            role_label = "Khách hàng" if msg.role == "user" else "Tư vấn viên AI"
            lines.append(f"{role_label}: {msg.content}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Prompt Engineering
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """
Bạn là tư vấn viên AI thông minh của sàn thương mại điện tử TDQ-ECM.
Nhiệm vụ của bạn là hỗ trợ khách hàng một cách thân thiện, chính xác và ngắn gọn.

Nguyên tắc:
1. Chỉ trả lời dựa trên thông tin trong [Ngữ cảnh] được cung cấp.
2. Nếu không tìm thấy thông tin, hãy nói: "Tôi chưa có thông tin về vấn đề này, vui lòng liên hệ hotline 1800-1234."
3. Trả lời bằng tiếng Việt, lịch sự và dễ hiểu.
4. Không bịa đặt thông tin về giá cả, chính sách mà không có trong ngữ cảnh.
""".strip()


def build_rag_prompt(
    query: str,
    context: str,
    session: ChatSession,
    behavior_insight: str = "",
) -> str:
    """
    Xây dựng prompt đầy đủ theo cấu trúc RAG:
      [System] → [Context] → [Behavior Hint] → [History] → [Query]
    """
    parts = [SYSTEM_PROMPT]

    parts.append(f"\n[Ngữ cảnh từ Knowledge Base]\n{context}")

    if behavior_insight:
        parts.append(f"\n[Gợi ý hành vi người dùng]\nKhách hàng đang ở trạng thái: {behavior_insight}")

    history_text = session.format_history()
    if history_text:
        parts.append(f"\n[Lịch sử hội thoại]\n{history_text}")

    parts.append(f"\n[Câu hỏi của khách hàng]\n{query}")
    parts.append("\n[Trả lời]")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# LLM Backend
# ---------------------------------------------------------------------------
def _call_gemini(prompt: str) -> str:
    """Gọi Gemini API để sinh câu trả lời."""
    try:
        response = _GEMINI_MODEL.generate_content(prompt)
        return response.text.strip()
    except Exception as exc:
        logger.warning(f"Gemini API call failed: {exc}")
        return None


def _rule_based_answer(context: str, query: str) -> str:
    """
    Fallback rule-based: Trả về câu trả lời đơn giản từ context tìm được.
    Được dùng khi LLM không khả dụng.
    """
    if not context or context.startswith("Không tìm thấy"):
        return (
            "Xin lỗi, tôi chưa có thông tin về vấn đề này. "
            "Vui lòng liên hệ hotline 1800-1234 hoặc email support@tdq-ecm.vn để được hỗ trợ."
        )
    # Lấy câu trả lời đầu tiên từ context (phần sau "A:")
    for line in context.split("\n"):
        if line.startswith("A:"):
            return line[2:].strip()
    return context[:500]  # Giới hạn 500 ký tự


# ---------------------------------------------------------------------------
# RAGChatbot – Main Class
# ---------------------------------------------------------------------------
class RAGChatbot:
    """
    RAG Chatbot tích hợp KnowledgeBase + BehaviorModel.

    Usage:
        chatbot = RAGChatbot()
        result  = chatbot.chat(
            user_message="Làm sao đổi trả hàng?",
            session_id="sess_abc",
            user_id="user_123",
            event_sequence=["search", "click", "add_to_cart"],
        )
    """

    def __init__(self):
        self.kb             = KnowledgeBase()
        self.behavior_model = UserBehaviorModel()
        self.sessions: dict[str, ChatSession] = {}
        logger.info("RAGChatbot initialized.")

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------
    def get_or_create_session(self, session_id: str, user_id: str = "guest") -> ChatSession:
        if session_id not in self.sessions:
            self.sessions[session_id] = ChatSession(
                session_id=session_id,
                user_id=user_id,
            )
        return self.sessions[session_id]

    def clear_session(self, session_id: str):
        self.sessions.pop(session_id, None)

    # ------------------------------------------------------------------
    # Core chat
    # ------------------------------------------------------------------
    def chat(
        self,
        user_message: str,
        session_id: str = "default",
        user_id: str = "guest",
        event_sequence: list = None,
        top_k: int = 3,
        use_rag: bool = True,
    ) -> dict:
        """
        Xử lý một lượt hội thoại.

        Args:
            user_message:   Câu hỏi của người dùng
            session_id:     ID phiên chat (dùng để lưu history)
            user_id:        ID người dùng (dùng để lấy behavior insight)
            event_sequence: Chuỗi hành vi gần đây (search/click/cart/...)
            top_k:          Số tài liệu truy vấn từ KB
            use_rag:        True = dùng RAG pipeline, False = mock

        Returns:
            {
              "answer": str,
              "sources": [{"id", "question", "score"}, ...],
              "behavior_insight": {...},
              "session_id": str,
            }
        """
        if not user_message or not user_message.strip():
            return {
                "answer": "Vui lòng nhập câu hỏi.",
                "sources": [],
                "behavior_insight": {},
                "session_id": session_id,
            }

        session = self.get_or_create_session(session_id, user_id)
        session.add("user", user_message)

        if not use_rag:
            answer = f"[No-RAG Mode] Câu hỏi nhận được: {user_message}"
            session.add("assistant", answer)
            return {"answer": answer, "sources": [], "behavior_insight": {}, "session_id": session_id}

        # ── Step 1: Retrieve ──────────────────────────────────────────
        search_results = self.kb.search(user_message, top_k=top_k)
        context        = self._format_context(search_results)

        # ── Step 2: Behavior Insight ──────────────────────────────────
        behavior_insight = {}
        behavior_hint    = ""
        if event_sequence:
            behavior_insight = self.behavior_model.predict_intent(event_sequence)
            behavior_hint    = behavior_insight.get("intent", "")

        # ── Step 3: Build Prompt ──────────────────────────────────────
        prompt = build_rag_prompt(
            query=user_message,
            context=context,
            session=session,
            behavior_insight=behavior_hint,
        )

        # ── Step 4: Generate ──────────────────────────────────────────
        answer = None
        if _GEMINI_AVAILABLE:
            answer = _call_gemini(prompt)
        if answer is None:
            answer = _rule_based_answer(context, user_message)

        session.add("assistant", answer)

        # ── Response ──────────────────────────────────────────────────
        return {
            "answer": answer,
            "sources": [
                {
                    "id":       r["id"],
                    "question": r["question"],
                    "score":    r["score"],
                }
                for r in search_results
            ],
            "behavior_insight": behavior_insight,
            "session_id": session_id,
        }

    # ------------------------------------------------------------------
    # Knowledge Base passthrough helpers
    # ------------------------------------------------------------------
    def add_knowledge(self, doc_data: dict):
        """Thêm tài liệu mới vào KB từ API."""
        from .knowledge_base import KnowledgeDocument
        doc = KnowledgeDocument(**doc_data)
        self.kb.add_document(doc)

    def search_knowledge(self, query: str, top_k: int = 5) -> list[dict]:
        return self.kb.search(query, top_k=top_k)

    def update_user_graph(self, user_id: str, product_id: str, event: str, category_id: str = ""):
        """Cập nhật đồ thị hành vi sau một tương tác."""
        self.kb.update_graph(user_id, product_id, event, category_id)

    def get_user_graph(self, user_id: str) -> dict:
        return self.kb.get_user_graph(user_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _format_context(search_results: list[dict]) -> str:
        if not search_results:
            return "Không tìm thấy thông tin phù hợp."
        parts = []
        for r in search_results:
            parts.append(f"Q: {r['question']}\nA: {r['answer']}")
        return "\n\n".join(parts)
