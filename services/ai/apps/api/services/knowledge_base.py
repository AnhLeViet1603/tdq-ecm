"""
knowledge_base.py
=================
Knowledge Base (KB) cho hệ thống tư vấn E-Commerce.

Thiết kế:
  ─────────────────────────────────────────────────────────────────────────────
  1. KnowledgeDocument   – Đơn vị lưu trữ: câu hỏi / câu trả lời / metadata
  2. GraphEdge           – Cạnh đồ thị giữa (User/Product/Category/Query)
  3. KnowledgeBase       – Lớp chính:
       a. FAISS Index     – Tìm kiếm ngữ nghĩa nhanh bằng vector embedding
       b. Graph Store     – Dict lưu trữ quan hệ đồ thị (neo4j-lite style)
       c. add_document()  – Thêm tài liệu mới vào KB
       d. search()        – Tìm kiếm ngữ nghĩa + keyword fallback
       e. get_context()   – Trả về context string cho RAG
       f. update_graph()  – Cập nhật đồ thị hành vi người dùng
  ─────────────────────────────────────────────────────────────────────────────

Tất cả dữ liệu KB được seed sẵn với FAQ + thông tin sản phẩm mẫu.
Trong production, tích hợp với product-service và interaction-service.
"""

import os
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MODEL_NAME  = "paraphrase-multilingual-MiniLM-L12-v2"   # Hỗ trợ tiếng Việt tốt hơn
KB_PATH     = os.path.join(os.path.dirname(__file__), "kb_store.json")

# Trọng số cạnh hành vi (α · clicks + β · cart + γ · purchase)
ALPHA = 0.3   # click weight
BETA  = 0.5   # cart weight
GAMMA = 1.0   # purchase weight


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------
@dataclass
class KnowledgeDocument:
    """Một tài liệu trong Knowledge Base."""
    id: str
    category: str          # faq / product / policy / promotion
    question: str
    answer: str
    keywords: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_index_text(self) -> str:
        """Text đưa vào FAISS index (question + keywords)."""
        return f"{self.question} {' '.join(self.keywords)}"


@dataclass
class GraphEdge:
    """Cạnh đồ thị biểu diễn mối quan hệ giữa hai node."""
    source: str       # e.g. "user_123"
    relation: str     # viewed / clicked / bought / searched / belongs_to / similar
    target: str       # e.g. "prod_456"
    weight: float = 1.0


# ---------------------------------------------------------------------------
# Seed Knowledge Documents
# ---------------------------------------------------------------------------
SEED_DOCUMENTS = [
    # ── FAQ: Đổi trả ──────────────────────────────────────────────────────
    KnowledgeDocument(
        id="faq_001",
        category="faq",
        question="Làm thế nào để đổi trả hàng?",
        answer=(
            "Bạn có thể đổi trả hàng trong vòng 7 ngày kể từ ngày nhận hàng "
            "nếu sản phẩm bị lỗi do nhà sản xuất. Vui lòng liên hệ hotline "
            "1800-1234 hoặc tạo yêu cầu trong mục 'Đơn hàng của tôi'."
        ),
        keywords=["đổi trả", "hoàn hàng", "lỗi", "bảo hành"],
        metadata={"category_id": 2},
    ),
    KnowledgeDocument(
        id="faq_002",
        category="faq",
        question="Hoàn tiền mất bao lâu?",
        answer=(
            "Sau khi nhận lại hàng đổi trả, chúng tôi xử lý hoàn tiền trong "
            "3-5 ngày làm việc vào tài khoản gốc hoặc ví điện tử của bạn."
        ),
        keywords=["hoàn tiền", "refund", "tiền", "thời gian hoàn"],
        metadata={"category_id": 2},
    ),
    # ── FAQ: Giao hàng ────────────────────────────────────────────────────
    KnowledgeDocument(
        id="faq_003",
        category="faq",
        question="Thời gian giao hàng là bao lâu?",
        answer=(
            "Đơn hàng nội thành TP.HCM và Hà Nội: 1-2 ngày làm việc. "
            "Các tỉnh thành khác: 3-5 ngày làm việc. "
            "Hàng nặng / cồng kềnh: 5-7 ngày làm việc."
        ),
        keywords=["giao hàng", "ship", "vận chuyển", "thời gian"],
        metadata={"category_id": 1},
    ),
    KnowledgeDocument(
        id="faq_004",
        category="faq",
        question="Phí vận chuyển như thế nào?",
        answer=(
            "Miễn phí vận chuyển cho đơn hàng từ 500.000đ. "
            "Đơn dưới 500.000đ: phí ship 30.000đ - 50.000đ tuỳ khu vực."
        ),
        keywords=["phí ship", "phí vận chuyển", "giao hàng miễn phí", "free ship"],
        metadata={"category_id": 1},
    ),
    # ── FAQ: Thanh toán ───────────────────────────────────────────────────
    KnowledgeDocument(
        id="faq_005",
        category="faq",
        question="Có những hình thức thanh toán nào?",
        answer=(
            "Chúng tôi hỗ trợ: Thẻ tín dụng/ghi nợ (Visa, Mastercard), "
            "Chuyển khoản ngân hàng, Ví điện tử (MoMo, ZaloPay, VNPay), "
            "Thanh toán khi nhận hàng (COD)."
        ),
        keywords=["thanh toán", "payment", "momo", "zalopay", "cod", "thẻ"],
        metadata={"category_id": 1},
    ),
    KnowledgeDocument(
        id="faq_006",
        category="faq",
        question="Làm sao để dùng mã giảm giá?",
        answer=(
            "Trong trang thanh toán, tìm ô 'Nhập mã giảm giá' và điền mã của bạn, "
            "sau đó nhấn 'Áp dụng'. Giảm giá sẽ được trừ trực tiếp vào tổng đơn hàng."
        ),
        keywords=["voucher", "mã giảm giá", "coupon", "khuyến mãi"],
        metadata={"category_id": 4},
    ),
    # ── FAQ: Tài khoản ────────────────────────────────────────────────────
    KnowledgeDocument(
        id="faq_007",
        category="faq",
        question="Quên mật khẩu phải làm thế nào?",
        answer=(
            "Nhấn 'Quên mật khẩu' trên trang đăng nhập. "
            "Nhập email đăng ký, hệ thống sẽ gửi link đặt lại mật khẩu trong vòng 5 phút."
        ),
        keywords=["quên mật khẩu", "đặt lại mật khẩu", "reset password", "tài khoản"],
        metadata={"category_id": 3},
    ),
    # ── Chính sách ────────────────────────────────────────────────────────
    KnowledgeDocument(
        id="policy_001",
        category="policy",
        question="Chính sách bảo mật thông tin cá nhân?",
        answer=(
            "Chúng tôi cam kết bảo mật thông tin cá nhân của khách hàng. "
            "Dữ liệu được mã hoá TLS và không chia sẻ với bên thứ ba khi chưa có sự đồng ý. "
            "Xem chi tiết tại /chinh-sach-bao-mat."
        ),
        keywords=["bảo mật", "riêng tư", "privacy", "dữ liệu cá nhân"],
        metadata={"category_id": 3},
    ),
    # ── Sản phẩm ──────────────────────────────────────────────────────────
    KnowledgeDocument(
        id="prod_001",
        category="product",
        question="Sản phẩm có bảo hành không?",
        answer=(
            "Tất cả sản phẩm điện tử đều có bảo hành 12 tháng chính hãng. "
            "Sản phẩm thời trang bảo hành 30 ngày lỗi vải/đường may."
        ),
        keywords=["bảo hành", "warranty", "chính hãng", "lỗi"],
        metadata={"category_id": 4},
    ),
    KnowledgeDocument(
        id="prod_002",
        category="product",
        question="Làm sao biết hàng có còn không?",
        answer=(
            "Trên trang sản phẩm sẽ hiển thị 'Còn hàng' hoặc 'Hết hàng'. "
            "Bạn có thể bấm 'Thông báo khi có hàng' để nhận email khi sản phẩm được nhập thêm."
        ),
        keywords=["còn hàng", "tình trạng", "hết hàng", "stock"],
        metadata={"category_id": 4},
    ),
]

FAQ_CATEGORIES = [
    {"id": 1, "name": "Thanh toán & Giao hàng", "icon": "🚚", "doc_ids": ["faq_003", "faq_004", "faq_005"]},
    {"id": 2, "name": "Đổi trả & Hoàn tiền",   "icon": "🔄", "doc_ids": ["faq_001", "faq_002"]},
    {"id": 3, "name": "Tài khoản & Bảo mật",   "icon": "🔒", "doc_ids": ["faq_007", "policy_001"]},
    {"id": 4, "name": "Sản phẩm",               "icon": "📦", "doc_ids": ["faq_006", "prod_001", "prod_002"]},
]


# ---------------------------------------------------------------------------
# KnowledgeBase
# ---------------------------------------------------------------------------
class KnowledgeBase:
    """
    Knowledge Base kết hợp:
      - FAISS vector index cho tìm kiếm ngữ nghĩa
      - Graph store cho quan hệ User-Product-Category
      - Keyword fallback khi FAISS không khả dụng
    """

    def __init__(self):
        self.documents: list[KnowledgeDocument] = []
        self.graph_edges: list[GraphEdge] = []
        # user_interest[user_id][product_id] = weighted score
        self.user_interest: dict[str, dict[str, float]] = {}

        self.encoder: Optional[SentenceTransformer] = None
        self.index: Optional[faiss.Index] = None
        self.dimension: int = 0
        self.ready: bool = False

        self._init_encoder()
        self._seed_documents()
        self._load_persisted_edges()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------
    def _init_encoder(self):
        try:
            self.encoder  = SentenceTransformer(MODEL_NAME)
            self.dimension = self.encoder.get_sentence_embedding_dimension()
            self.index     = faiss.IndexFlatL2(self.dimension)
            self.ready     = True
            logger.info(f"SentenceTransformer '{MODEL_NAME}' loaded. dim={self.dimension}")
        except Exception as exc:
            logger.warning(f"Cannot load SentenceTransformer: {exc}. Falling back to keyword search.")

    def _seed_documents(self):
        """Nạp tài liệu mẫu vào KB."""
        for doc in SEED_DOCUMENTS:
            self._add_to_index(doc)
            self.documents.append(doc)
        logger.info(f"Seeded {len(self.documents)} documents into KB.")

    def _load_persisted_edges(self):
        """Tải graph edges đã lưu từ file JSON (nếu có)."""
        if os.path.exists(KB_PATH):
            try:
                with open(KB_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.graph_edges = [GraphEdge(**e) for e in data.get("edges", [])]
                self.user_interest = data.get("user_interest", {})
                logger.info(f"Loaded {len(self.graph_edges)} saved graph edges.")
            except Exception as exc:
                logger.warning(f"Failed to load KB store: {exc}")

    def _persist_edges(self):
        """Lưu graph edges ra file JSON."""
        try:
            with open(KB_PATH, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "edges": [asdict(e) for e in self.graph_edges],
                        "user_interest": self.user_interest,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as exc:
            logger.warning(f"Failed to persist KB store: {exc}")

    # ------------------------------------------------------------------
    # Document Management
    # ------------------------------------------------------------------
    def _add_to_index(self, doc: KnowledgeDocument):
        if self.ready:
            text = doc.to_index_text()
            vec  = self.encoder.encode([text]).astype("float32")
            self.index.add(vec)

    def add_document(self, doc: KnowledgeDocument):
        """Thêm tài liệu mới vào KB tại runtime."""
        self._add_to_index(doc)
        self.documents.append(doc)
        logger.info(f"Added document id={doc.id} to KB.")

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    def search(self, query: str, top_k: int = 3, threshold: float = 1.5) -> list[dict]:
        """
        Tìm kiếm ngữ nghĩa trong KB.

        Returns:
            list of { "id", "category", "question", "answer", "score" }
        """
        if self.ready and self.documents:
            return self._semantic_search(query, top_k, threshold)
        return self._keyword_search(query, top_k)

    def _semantic_search(self, query: str, top_k: int, threshold: float) -> list[dict]:
        q_vec = self.encoder.encode([query]).astype("float32")
        actual_k = min(top_k, len(self.documents))
        distances, indices = self.index.search(q_vec, actual_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1 or idx >= len(self.documents):
                continue
            doc = self.documents[idx]
            results.append({
                "id":       doc.id,
                "category": doc.category,
                "question": doc.question,
                "answer":   doc.answer,
                "score":    round(float(dist), 4),
            })
        return results

    def _keyword_search(self, query: str, top_k: int) -> list[dict]:
        query_lower = query.lower()
        results = []
        for doc in self.documents:
            text = (doc.question + " " + " ".join(doc.keywords)).lower()
            if query_lower in text:
                results.append({
                    "id":       doc.id,
                    "category": doc.category,
                    "question": doc.question,
                    "answer":   doc.answer,
                    "score":    0.0,
                })
                if len(results) >= top_k:
                    break
        return results

    def get_context(self, query: str, top_k: int = 3) -> str:
        """
        Trả về context string dùng cho RAG pipeline.
        Format: "Q: ... \nA: ..." cho mỗi document tìm được.
        """
        results = self.search(query, top_k=top_k)
        if not results:
            return "Không tìm thấy thông tin phù hợp."
        parts = []
        for r in results:
            parts.append(f"Q: {r['question']}\nA: {r['answer']}")
        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Graph Operations
    # ------------------------------------------------------------------
    def update_graph(
        self,
        user_id: str,
        product_id: str,
        event: str,           # "search" | "click" | "add_to_cart" | "purchase"
        category_id: str = "",
    ):
        """
        Cập nhật đồ thị tri thức sau một hành vi người dùng.
        Tính weighted edge: w = α·clicks + β·cart + γ·purchase
        """
        # Thêm cạnh U → P
        edge = GraphEdge(
            source=f"user_{user_id}",
            relation=event,
            target=f"prod_{product_id}",
        )
        self.graph_edges.append(edge)

        # Cập nhật interest score
        if user_id not in self.user_interest:
            self.user_interest[user_id] = {}
        current = self.user_interest[user_id].get(product_id, 0.0)
        delta = {"search": 0.1, "click": ALPHA, "add_to_cart": BETA, "purchase": GAMMA}.get(event, 0.0)
        self.user_interest[user_id][product_id] = round(current + delta, 4)

        # Thêm cạnh P → C nếu có category
        if category_id:
            cat_edge = GraphEdge(
                source=f"prod_{product_id}",
                relation="belongs_to",
                target=f"cat_{category_id}",
            )
            self.graph_edges.append(cat_edge)

        self._persist_edges()

    def get_user_graph(self, user_id: str) -> dict:
        """Trả về tất cả cạnh liên quan đến user_id."""
        prefix = f"user_{user_id}"
        edges  = [asdict(e) for e in self.graph_edges if e.source == prefix]
        interests = self.user_interest.get(user_id, {})
        return {
            "user_id":   user_id,
            "edges":     edges,
            "interests": dict(sorted(interests.items(), key=lambda x: x[1], reverse=True)),
        }

    def get_top_interest_products(self, user_id: str, top_k: int = 5) -> list[str]:
        """Trả về danh sách product_id đượcinterest nhiều nhất."""
        interests = self.user_interest.get(user_id, {})
        sorted_prods = sorted(interests.items(), key=lambda x: x[1], reverse=True)
        return [pid for pid, _ in sorted_prods[:top_k]]

    # ------------------------------------------------------------------
    # FAQ Categories
    # ------------------------------------------------------------------
    def get_faq_categories(self) -> list[dict]:
        return FAQ_CATEGORIES

    def get_faq_by_category(self, category_id: int) -> list[dict]:
        cat = next((c for c in FAQ_CATEGORIES if c["id"] == category_id), None)
        if not cat:
            return []
        doc_ids = cat.get("doc_ids", [])
        return [
            {"id": d.id, "question": d.question, "answer": d.answer}
            for d in self.documents
            if d.id in doc_ids
        ]
