"""
=============================================================
PHẦN 4 – Hệ thống GraphRAG: Ngôn ngữ tự nhiên → Cypher → Neo4j → Gemini
Môn: AI SERVICE
=============================================================
pip install neo4j google-generativeai langchain langchain-google-genai
=============================================================
Gemini API Key: AIzaSyDxqxtaY0j34jqfhbPLtCA38Ws07l5q45k
=============================================================
"""

import os
import re
import time
from neo4j import GraphDatabase

# ── Cấu hình Gemini ─────────────────────────────────────────
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDxqxtaY0j34jqfhbPLtCA38Ws07l5q45k")
genai.configure(api_key=GEMINI_API_KEY)
llm = genai.GenerativeModel("gemini-2.0-flash")

# ── Cấu hình Neo4j ──────────────────────────────────────────
NEO4J_URI      = os.getenv("NEO4J_URI",      "neo4j://127.0.0.1:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "admin123")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


# ════════════════════════════════════════════════════════════
# Schema mô tả graph để LLM sinh Cypher đúng cấu trúc
# ════════════════════════════════════════════════════════════
GRAPH_SCHEMA = """
Graph Schema của hệ thống E-Commerce:

Nodes:
  - (:User   {id: string})       — Người dùng, ví dụ: U001, U002
  - (:Product {id: string})      — Sản phẩm,   ví dụ: P001, P100

Relationships (có thuộc tính timestamp: string 'YYYY-MM-DD HH:MM:SS'):
  - (u:User)-[:VIEWED]->         (p:Product)  — Người dùng đã xem sản phẩm
  - (u:User)-[:CLICKED]->        (p:Product)  — Người dùng đã click vào sản phẩm
  - (u:User)-[:ADDED_TO_CART]--> (p:Product)  — Người dùng đã thêm vào giỏ hàng

Ràng buộc:
  - user_id có dạng U + 3 chữ số (U001 … U500)
  - product_id có dạng P + 3 chữ số (P001 … P200)
"""


# ════════════════════════════════════════════════════════════
# 1. Text → Cypher  (Gemini làm NL2Cypher)
# ════════════════════════════════════════════════════════════
def text_to_cypher(question: str) -> str:
    """
    Dùng Gemini để chuyển câu hỏi ngôn ngữ tự nhiên → câu Cypher.
    Chỉ trả về đúng câu Cypher, không có giải thích.
    """
    prompt = f"""Bạn là chuyên gia Neo4j Cypher. Dựa trên schema sau, hãy viết một câu Cypher
để trả lời câu hỏi của người dùng. CHỈ trả về câu Cypher thuần túy, không markdown, không giải thích.

{GRAPH_SCHEMA}

Câu hỏi: {question}

Cypher:"""

    response = llm.generate_content(prompt)
    raw = response.text.strip()

    # Loại bỏ markdown code fence nếu có
    raw = re.sub(r"```(?:cypher)?", "", raw, flags=re.IGNORECASE).replace("```", "").strip()
    return raw


# ════════════════════════════════════════════════════════════
# 2. Cypher → Kết quả Neo4j
# ════════════════════════════════════════════════════════════
def execute_cypher(cypher: str) -> list[dict]:
    """Thực thi Cypher và trả về danh sách record dạng dict."""
    try:
        with driver.session() as session:
            result = session.run(cypher)
            return [dict(r) for r in result]
    except Exception as e:
        return [{"error": str(e)}]


# ════════════════════════════════════════════════════════════
# 3. Kết quả + câu hỏi → Câu trả lời tiếng Việt
# ════════════════════════════════════════════════════════════
def generate_answer(question: str, cypher: str, records: list[dict]) -> str:
    """Gemini tổng hợp kết quả thô thành câu trả lời tự nhiên."""
    records_text = "\n".join(str(r) for r in records[:20])  # Giới hạn 20 dòng

    prompt = f"""Bạn là trợ lý AI thông minh của sàn thương mại điện tử TDQ-ECM.
Dựa trên kết quả truy vấn từ cơ sở dữ liệu đồ thị Neo4j, hãy trả lời câu hỏi bằng tiếng Việt
một cách rõ ràng và thân thiện. Nếu kết quả rỗng, hãy nói không có dữ liệu.

Câu hỏi: {question}

Câu truy vấn đã chạy:
{cypher}

Kết quả từ Neo4j:
{records_text}

Trả lời:"""

    response = llm.generate_content(prompt)
    return response.text.strip()


# ════════════════════════════════════════════════════════════
# 4. GraphRAG Pipeline hoàn chỉnh
# ════════════════════════════════════════════════════════════
def graph_rag(question: str, verbose: bool = True) -> dict:
    """
    Pipeline 3 bước:
      1. NL → Cypher  (Gemini LLM)
      2. Cypher → Neo4j records
      3. Records → Natural language answer  (Gemini LLM)
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"❓ Câu hỏi: {question}")
        print("─" * 60)

    # Bước 1: Sinh Cypher
    cypher = text_to_cypher(question)
    if verbose:
        print(f"📝 Cypher sinh ra:\n{cypher}")
        print("─" * 60)

    # Bước 2: Thực thi Neo4j
    records = execute_cypher(cypher)
    if verbose:
        print(f"📊 {len(records)} records từ Neo4j")
        if records and "error" not in records[0]:
            for r in records[:5]:
                print(f"   {r}")

    # Bước 3: Sinh câu trả lời
    answer = generate_answer(question, cypher, records)
    if verbose:
        print("─" * 60)
        print(f"💬 Trả lời:\n{answer}")
        print("=" * 60)

    return {
        "question": question,
        "cypher":   cypher,
        "records":  records,
        "answer":   answer,
    }


# ════════════════════════════════════════════════════════════
# 5. Demo – chạy thử với 5 câu hỏi mẫu
# ════════════════════════════════════════════════════════════
DEMO_QUESTIONS = [
    "User U001 đã click vào những sản phẩm nào?",
    "Sản phẩm nào được thêm vào giỏ hàng nhiều nhất?",
    "User U050 đã xem những sản phẩm nào?",
    "Liệt kê 5 user có nhiều hành vi add_to_cart nhất.",
    "Sản phẩm P025 đã được bao nhiêu người dùng click vào?",
]

if __name__ == "__main__":
    print("\n" + "█"*60)
    print("  DEMO GRAPHRAG – Hệ thống hỏi đáp trên Knowledge Graph")
    print("█"*60)

    results = []
    for q in DEMO_QUESTIONS:
        result = graph_rag(q, verbose=True)
        results.append(result)
        # Nghỉ 5 giây giữa các câu hỏi để tránh Rate Limit (429) của gói Gemini Free
        print("\n⏳ Nghỉ 5 giây để tránh lỗi Rate Limit của API...")
        time.sleep(5)

    driver.close()
    print("\n✅ GraphRAG demo hoàn tất. Neo4j connection đã đóng.")

    # ─── In tài liệu giải thích GraphRAG (dùng cho báo cáo) ────
    DOC = """
╔══════════════════════════════════════════════════════════════════╗
║    TÀI LIỆU: CƠ CHẾ HOẠT ĐỘNG CỦA GRAPHRAG TRONG DỰ ÁN        ║
╚══════════════════════════════════════════════════════════════════╝

GraphRAG (Graph-based Retrieval-Augmented Generation) là sự kết hợp
của hai kỹ thuật tiên tiến: truy xuất thông tin từ đồ thị tri thức
(Knowledge Graph) và sinh ngôn ngữ tự nhiên bằng mô hình ngôn ngữ
lớn (LLM). Trong dự án TDQ-ECM, hệ thống GraphRAG hoạt động qua
ba giai đoạn tuần tự như sau:

**Giai đoạn 1 – NL2Cypher (Natural Language → Cypher Query):**
Người dùng đặt câu hỏi bằng tiếng Việt thông thường (ví dụ: "User
U001 đã click vào những sản phẩm nào?"). Gemini 1.5-Flash nhận câu
hỏi cùng với schema mô tả cấu trúc đồ thị (Nodes: User, Product;
Relationships: VIEWED, CLICKED, ADDED_TO_CART) và sinh ra câu truy
vấn Cypher tương ứng. Đây là bước "dịch" then chốt, giúp hệ thống
không cần người dùng biết ngôn ngữ truy vấn đồ thị.

**Giai đoạn 2 – Graph Retrieval (Truy xuất Neo4j):**
Câu Cypher được thực thi trực tiếp trên cơ sở dữ liệu đồ thị Neo4j,
nơi chứa toàn bộ dữ liệu hành vi người dùng được nhập từ CSV
(~8 000+ bản ghi). Kết quả trả về là danh sách các record (dict)
chứa thông tin thực tế: user_id, product_id, timestamp, v.v.

**Giai đoạn 3 – Answer Generation (Sinh câu trả lời):**
Kết quả thô từ Neo4j được đưa vào một prompt kết hợp với câu
hỏi gốc. Gemini tổng hợp thông tin này thành câu trả lời tự nhiên,
thân thiện và bằng tiếng Việt, phù hợp để hiển thị trên giao diện
chat của ứng dụng e-commerce.

**Ưu điểm của GraphRAG so với RAG truyền thống:**
Trong khi RAG thông thường tìm kiếm trong tập văn bản phẳng (FAISS),
GraphRAG khám phá mạng lưới quan hệ đa chiều: User–Product–Category.
Điều này cho phép hệ thống trả lời các câu hỏi phức tạp về hành vi
người dùng, chuỗi tương tác, và phân tích xu hướng mua sắm mà RAG
truyền thống không thể xử lý.
╚══════════════════════════════════════════════════════════════════╝
"""
    print(DOC)
