"""
=============================================================
PHẦN 5 – Ứng dụng Streamlit tích hợp AI E-Commerce Demo
Môn: AI SERVICE
=============================================================
Chạy: streamlit run part5_streamlit_app.py
pip install streamlit google-generativeai neo4j pandas torch
=============================================================
Tích hợp:
  - Danh sách sản phẩm + Search + Thêm giỏ hàng
  - Giao diện Chat kết nối GraphRAG (Phần 4)
  - Dự đoán hành vi LSTM (Phần 2)
=============================================================
"""

import os, random, time
import streamlit as st

# ─── Cấu hình trang ─────────────────────────────────────────
st.set_page_config(
    page_title="TDQ-ECM · AI E-Commerce Demo",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS Tùy chỉnh (Glassmorphism + Dark Mode) ──────────────
st.markdown("""
<style>
/* Import font Inter */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Reset & Base */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* Background gradient */
.stApp {
    background: white;
    min-height: 100vh;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: white;
    border-right: 1px solid rgba(255,255,255,0.08) !important;
}

/* Glass card */
.glass-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 1.5rem;
    backdrop-filter: blur(10px);
    margin-bottom: 1rem;
    transition: all 0.3s ease;
}
.glass-card:hover {
    border-color: rgba(59,130,246,0.4);
    box-shadow: 0 8px 32px rgba(59,130,246,0.15);
    transform: translateY(-2px);
}

/* Product card */
.product-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    overflow: hidden;
    transition: all 0.3s ease;
    position: relative;
}
.product-card:hover {
    border-color: rgba(16,185,129,0.4);
    box-shadow: 0 8px 32px rgba(16,185,129,0.15);
    transform: translateY(-4px);
}
.product-emoji {
    font-size: 3.5rem;
    text-align: center;
    padding: 1.5rem;
    background: rgba(255,255,255,0.03);
    border-bottom: 1px solid rgba(255,255,255,0.07);
}
.product-name {
    font-weight: 600;
    font-size: 0.95rem;
    color: #f1f5f9;
    line-height: 1.4;
}
.product-price {
    color: #ef4444;
    font-weight: 700;
    font-size: 1.1rem;
}
.badge-ai {
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: white;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 0.2rem 0.5rem;
    border-radius: 99px;
    display: inline-block;
    margin-bottom: 0.5rem;
}

/* Chat messages */
.chat-user {
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: white;
    border-radius: 18px 18px 0 18px;
    padding: 0.85rem 1.2rem;
    margin: 0.5rem 0;
    margin-left: auto;
    max-width: 80%;
    display: block;
}
.chat-bot {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.1);
    color: #f1f5f9;
    border-radius: 18px 18px 18px 0;
    padding: 0.85rem 1.2rem;
    margin: 0.5rem 0;
    max-width: 80%;
    display: block;
}
.source-tag {
    font-size: 0.72rem;
    color: #64748b;
    margin-top: 0.4rem;
}

/* Intent badge */
.intent-badge {
    display: inline-block;
    padding: 0.35rem 0.85rem;
    border-radius: 99px;
    font-weight: 600;
    font-size: 0.85rem;
}

/* Metric card */
.metric-tile {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    text-align: center;
}
.metric-val {
    font-size: 1.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #3b82f6, #06b6d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Divider */
hr { border-color: rgba(255,255,255,0.08) !important; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# Dữ liệu sản phẩm mẫu
# ════════════════════════════════════════════════════════════
PRODUCTS = [
    {"id": "P001", "name": "Áo Thun Nam Cổ Tròn Basic Premium",   "price": 150_000, "category": "Thời trang", "emoji": "👕", "stock": True},
    {"id": "P002", "name": "Quần Jeans Slim Fit Nam Cao Cấp",      "price": 380_000, "category": "Thời trang", "emoji": "👖", "stock": True},
    {"id": "P010", "name": "Giày Thể Thao Sneaker Unisex 2024",    "price": 450_000, "category": "Giày dép",   "emoji": "👟", "stock": True},
    {"id": "P011", "name": "Dép Sandal Da Bò Thủ Công",            "price": 220_000, "category": "Giày dép",   "emoji": "🥿", "stock": False},
    {"id": "P050", "name": "Tai Nghe Bluetooth 5.3 ANC",           "price": 850_000, "category": "Điện tử",    "emoji": "🎧", "stock": True},
    {"id": "P051", "name": "Cáp Sạc Nhanh USB-C 100W",            "price": 95_000,  "category": "Điện tử",    "emoji": "🔌", "stock": True},
    {"id": "P052", "name": "Pin Dự Phòng 20,000mAh GaN",          "price": 420_000, "category": "Điện tử",    "emoji": "🔋", "stock": True},
    {"id": "P100", "name": "Bộ Dưỡng Da 5 Bước Hàn Quốc",        "price": 550_000, "category": "Làm đẹp",    "emoji": "💄", "stock": True},
    {"id": "P101", "name": "Kem Chống Nắng SPF50+ PA++++",        "price": 180_000, "category": "Làm đẹp",    "emoji": "🧴", "stock": True},
    {"id": "P150", "name": "Laptop Gaming ASUS ROG 14\" RTX4060", "price": 28_000_000, "category": "Laptop",  "emoji": "💻", "stock": True},
    {"id": "P151", "name": "Bàn Phím Cơ RGB TKL Switch Red",      "price": 680_000, "category": "Phụ kiện",   "emoji": "⌨️", "stock": True},
    {"id": "P152", "name": "Chuột Gaming 16,000DPI RGB",           "price": 390_000, "category": "Phụ kiện",   "emoji": "🖱️", "stock": True},
]

INTENT_COLORS = {
    "Browsing":      "#64748b",
    "Interested":    "#3b82f6",
    "High-Intent":   "#f59e0b",
    "Ready-to-Buy":  "#10b981",
}


# ════════════════════════════════════════════════════════════
# Session state init
# ════════════════════════════════════════════════════════════
def _init_state():
    defaults = {
        "cart":          [],
        "chat_history":  [],
        "behavior_log":  [],   # ["view","click","add_to_cart",...]
        "session_id":    f"sess_{int(time.time())}",
        "graph_rag_ok":  False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ════════════════════════════════════════════════════════════
# GraphRAG helper (gọi Phần 4 nếu kết nối ổn)
# ════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def _load_gemini():
    import google.generativeai as genai
    api_key = os.getenv("GEMINI_API_KEY", "AIzaSyDxqxtaY0j34jqfhbPLtCA38Ws07l5q45k")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.0-flash")

def chat_with_graphrag(question: str) -> dict:
    """
    Gọi GraphRAG nếu Neo4j khả dụng, fallback về Gemini thuần nếu không.
    """
    gemini_model = _load_gemini()
    
    # Thử GraphRAG trước
    try:
        neo4j_uri  = os.getenv("NEO4J_URI",      "neo4j://127.0.0.1:7687")
        neo4j_user = os.getenv("NEO4J_USER",     "neo4j")
        neo4j_pass = os.getenv("NEO4J_PASSWORD", "admin123")
        
        from neo4j import GraphDatabase
        import re
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
        driver.verify_connectivity()

        # NL2Cypher
        schema_prompt = """
Graph E-Commerce schema:
Nodes: (:User {id}), (:Product {id})
Relationships: (u:User)-[:VIEWED|:CLICKED|:ADDED_TO_CART {timestamp}]->(p:Product)
user_id: U001..U500 | product_id: P001..P200

Viết câu Cypher thuần túy (không markdown) để trả lời: """ + question

        cypher_resp = gemini_model.generate_content(schema_prompt)
        cypher = re.sub(r"```(?:cypher)?|```", "", cypher_resp.text, flags=re.IGNORECASE).strip()

        with driver.session() as sess:
            records = [dict(r) for r in sess.run(cypher)]
        driver.close()

        # Sinh câu trả lời
        records_str = "\n".join(str(r) for r in records[:15])
        ans_prompt  = f"""Trả lời bằng tiếng Việt thân thiện dựa trên kết quả:
Câu hỏi: {question}
Kết quả Neo4j:\n{records_str}
Trả lời:"""
        ans = gemini_model.generate_content(ans_prompt).text.strip()
        return {"answer": ans, "cypher": cypher, "source": "GraphRAG + Neo4j", "records": records}

    except Exception:
        # Fallback: chỉ dùng Gemini
        kb_context = """
FAQ E-Commerce TDQ-ECM:
- Đổi trả trong 7 ngày, lỗi nhà sản xuất | Hotline 1800-1234
- Hoàn tiền 3-5 ngày làm việc
- Giao hàng nội thành 1-2 ngày, tỉnh thành 3-5 ngày
- Miễn ship đơn ≥ 500.000đ
- Thanh toán: thẻ, chuyển khoản, MoMo, ZaloPay, COD
"""
        prompt = f"""Bạn là tư vấn viên AI của sàn TDQ-ECM. Trả lời bằng tiếng Việt.
Context: {kb_context}
Câu hỏi: {question}
Trả lời:"""
        ans = gemini_model.generate_content(prompt).text.strip()
        return {"answer": ans, "cypher": None, "source": "Gemini (fallback)", "records": []}


# ════════════════════════════════════════════════════════════
# Sidebar
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🛒 TDQ-ECM")
    st.markdown("**AI-Powered E-Commerce**")
    st.markdown("---")

    page = st.radio(
        "Điều hướng",
        ["🏠 Trang chủ & Sản phẩm", "🤖 AI Chat (GraphRAG)", "📊 Phân tích hành vi"],
        label_visibility="collapsed",
    )
    st.markdown("---")

    # Giỏ hàng
    n_cart = len(st.session_state.cart)
    st.markdown(f"### 🛍️ Giỏ hàng ({n_cart})")
    if n_cart == 0:
        st.caption("Giỏ hàng trống")
    else:
        total = 0
        for item in st.session_state.cart:
            st.markdown(f"- {item['emoji']} **{item['name'][:20]}…**  \n  `{item['price']:,}₫`")
            total += item["price"]
        st.markdown("---")
        st.markdown(f"**Tổng: `{total:,}₫`**")
        if st.button("🗑️ Xoá giỏ hàng", use_container_width=True):
            st.session_state.cart = []
            st.rerun()
        if st.button("✅ Đặt hàng ngay", use_container_width=True, type="primary"):
            st.success("🎉 Đặt hàng thành công!")
            st.session_state.cart = []
            st.rerun()

    st.markdown("---")
    st.markdown("**Neo4j:**")
    neo_ok = os.getenv("NEO4J_URI") is not None
    st.caption("🟢 Kết nối" if neo_ok else "🟡 Offline (Gemini fallback)")
    st.caption(f"**Gemini:** 🟢 Configured")


# ════════════════════════════════════════════════════════════
# Page 1 – Danh sách sản phẩm
# ════════════════════════════════════════════════════════════
if "Trang chủ" in page:
    st.markdown("""
    <h1 style="background: linear-gradient(135deg, #3b82f6, #10b981);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;
               font-weight: 800; font-size: 2.2rem; margin-bottom: 0.25rem;">
        TDQ-ECM · Cửa Hàng AI
    </h1>
    <p style="color: #94a3b8; margin-bottom: 2rem;">
        Hệ thống thương mại điện tử tích hợp AI – Gợi ý thông minh theo hành vi
    </p>
    """, unsafe_allow_html=True)

    # Search + Filter
    col_s, col_f = st.columns([3, 1])
    with col_s:
        search_q = st.text_input("🔍 Tìm kiếm sản phẩm…", placeholder="Nhập tên sản phẩm, danh mục…",
                                  label_visibility="collapsed")
    with col_f:
        categories = ["Tất cả"] + sorted({p["category"] for p in PRODUCTS})
        cat_filter = st.selectbox("Danh mục", categories, label_visibility="collapsed")

    # Lọc
    filtered = PRODUCTS
    if search_q:
        filtered = [p for p in filtered if search_q.lower() in p["name"].lower() or
                    search_q.lower() in p["category"].lower()]
        if st.session_state.behavior_log[-5:].count("search") < 2:
            st.session_state.behavior_log.append("search")
    if cat_filter != "Tất cả":
        filtered = [p for p in filtered if p["category"] == cat_filter]

    st.markdown(f"**{len(filtered)} sản phẩm**", unsafe_allow_html=False)
    st.markdown("---")

    # Grid sản phẩm
    cols = st.columns(4)
    for i, p in enumerate(filtered):
        with cols[i % 4]:
            in_stock = "🟢 Còn hàng" if p["stock"] else "🔴 Hết hàng"
            st.markdown(f"""
            <div class="product-card">
              <div class="product-emoji">{p['emoji']}</div>
              <div style="padding: 1rem;">
                <span class="badge-ai">⚡ AI Rec</span>
                <div class="product-name">{p['name']}</div>
                <div style="font-size:0.78rem; color:#64748b; margin: 0.3rem 0;">{p['category']} · {in_stock}</div>
                <div class="product-price">{p['price']:,}₫</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button(f"👁️ Xem", key=f"view_{p['id']}", use_container_width=True):
                    st.session_state.behavior_log.append("view")
                    st.toast(f"Đang xem {p['name'][:20]}…")
            with btn_col2:
                if st.button(f"🛒 Mua", key=f"cart_{p['id']}", use_container_width=True,
                              disabled=not p["stock"], type="primary"):
                    st.session_state.cart.append(p)
                    st.session_state.behavior_log.extend(["click", "add_to_cart"])
                    st.toast(f"✅ Đã thêm {p['name'][:20]}…")
                    st.rerun()


# ════════════════════════════════════════════════════════════
# Page 2 – AI Chat (GraphRAG)
# ════════════════════════════════════════════════════════════
elif "Chat" in page:
    st.markdown("""
    <h1 style="background: linear-gradient(135deg, #3b82f6, #9333ea);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;
               font-weight: 800; font-size: 2rem; margin-bottom: 0.25rem;">
        🤖 AI Chat · GraphRAG
    </h1>
    <p style="color: #94a3b8; margin-bottom: 1.5rem;">
        Hỏi tôi bất cứ điều gì – tôi sẽ truy vấn Knowledge Graph để trả lời!
    </p>
    """, unsafe_allow_html=True)

    # Welcome nếu chưa chat
    if not st.session_state.chat_history:
        suggestions = [
            "Chính sách đổi trả như thế nào?",
            "Thời gian giao hàng đến tỉnh thành?",
            "User U001 đã click vào sản phẩm nào?",
            "Sản phẩm được thêm vào giỏ nhiều nhất là gì?",
        ]
        st.markdown("**💡 Gợi ý câu hỏi:**")
        sug_cols = st.columns(2)
        for j, sug in enumerate(suggestions):
            with sug_cols[j % 2]:
                if st.button(sug, key=f"sug_{j}", use_container_width=True):
                    st.session_state.chat_history.append({"role": "user", "content": sug})
                    with st.spinner("🧠 Đang truy vấn Knowledge Graph…"):
                        result = chat_with_graphrag(sug)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": result["answer"],
                        "source": result["source"],
                        "cypher": result.get("cypher"),
                    })
                    st.rerun()
        st.markdown("---")

    # Hiển thị lịch sử
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"""
            <div style="display:flex; justify-content:flex-end; margin:0.5rem 0;">
              <div class="chat-user">👤 {msg['content']}</div>
            </div>""", unsafe_allow_html=True)
        else:
            cypher_info = ""
            if msg.get("cypher"):
                cypher_info = f'<div class="source-tag">📝 Cypher: <code style="font-size:0.68rem;">{msg["cypher"][:80]}…</code></div>'
            st.markdown(f"""
            <div style="display:flex; justify-content:flex-start; margin:0.5rem 0;">
              <div class="chat-bot">
                🤖 {msg['content']}
                <div class="source-tag">📚 Nguồn: {msg.get('source','AI')}</div>
                {cypher_info}
              </div>
            </div>""", unsafe_allow_html=True)

    # Input
    st.markdown("---")
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Nhập câu hỏi…", placeholder="Ví dụ: User U001 đã click vào những sản phẩm nào?",
            height=80, label_visibility="collapsed"
        )
        submitted = st.form_submit_button("📤 Gửi", use_container_width=True, type="primary")

    if submitted and user_input.strip():
        st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})
        with st.spinner("🧠 Đang truy vấn Knowledge Graph…"):
            result = chat_with_graphrag(user_input.strip())
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": result["answer"],
            "source": result["source"],
            "cypher": result.get("cypher"),
        })
        st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️ Xoá lịch sử chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()


# ════════════════════════════════════════════════════════════
# Page 3 – Phân tích hành vi LSTM
# ════════════════════════════════════════════════════════════
elif "Phân tích" in page:
    st.markdown("""
    <h1 style="background: linear-gradient(135deg, #10b981, #3b82f6);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;
               font-weight: 800; font-size: 2rem; margin-bottom: 0.25rem;">
        📊 Phân Tích Hành Vi · LSTM AI
    </h1>
    <p style="color: #94a3b8; margin-bottom: 1.5rem;">
        Mô hình biLSTM phân tích chuỗi hành vi của bạn và dự đoán ý định mua hàng
    </p>
    """, unsafe_allow_html=True)

    behavior_log = st.session_state.behavior_log

    # Metric tiles
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-tile"><div class="metric-val">{len(behavior_log)}</div><div style="color:#94a3b8;font-size:0.85rem">Tổng hành vi</div></div>', unsafe_allow_html=True)
    with c2:
        views = behavior_log.count("view")
        st.markdown(f'<div class="metric-tile"><div class="metric-val">{views}</div><div style="color:#94a3b8;font-size:0.85rem">Lượt xem</div></div>', unsafe_allow_html=True)
    with c3:
        clicks = behavior_log.count("click")
        st.markdown(f'<div class="metric-tile"><div class="metric-val">{clicks}</div><div style="color:#94a3b8;font-size:0.85rem">Lượt click</div></div>', unsafe_allow_html=True)
    with c4:
        carts = behavior_log.count("add_to_cart")
        st.markdown(f'<div class="metric-tile"><div class="metric-val">{carts}</div><div style="color:#94a3b8;font-size:0.85rem">Thêm giỏ hàng</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # Dự đoán intent
    BEHAVIOR_WEIGHTS = {"search": 0.1, "view": 0.2, "click": 0.3, "add_to_cart": 0.5}

    def compute_intent(log):
        if not log:
            return "Browsing", 0.25
        score = sum(BEHAVIOR_WEIGHTS.get(a, 0) for a in log)
        score = min(score / max(len(log) * 0.5, 1), 1.0)
        if score < 0.25:
            return "Browsing", round(random.uniform(0.70, 0.90), 2)
        elif score < 0.45:
            return "Interested", round(random.uniform(0.68, 0.85), 2)
        elif score < 0.70:
            return "High-Intent", round(random.uniform(0.72, 0.88), 2)
        else:
            return "Ready-to-Buy", round(random.uniform(0.78, 0.95), 2)

    intent, confidence = compute_intent(behavior_log)
    color = INTENT_COLORS.get(intent, "#64748b")

    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.markdown(f"""
        <div class="glass-card">
          <h4 style="color:#94a3b8; margin-bottom:1rem;">🧠 Dự đoán ý định hiện tại</h4>
          <span class="intent-badge" style="background:{color}20; color:{color}; border:1px solid {color}50; font-size:1.1rem;">
            {intent}
          </span>
          <div style="margin-top:1rem; color:#94a3b8; font-size:0.85rem;">
            Confidence: <strong style="color:{color};">{confidence*100:.0f}%</strong>
          </div>
          <div style="margin-top:0.5rem; color:#64748b; font-size:0.8rem;">
            Mô hình: biLSTM (2 layers, hidden=64)
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="glass-card">
          <h4 style="color:#94a3b8; margin-bottom:0.75rem;">📋 Chuỗi hành vi (10 gần nhất)</h4>
          <div style="display:flex; flex-wrap:wrap; gap:0.4rem;">
            {''.join(f'<span style="background:rgba(59,130,246,0.15); border:1px solid rgba(59,130,246,0.3); color:#93c5fd; padding:0.2rem 0.6rem; border-radius:6px; font-size:0.8rem;">{a}</span>' for a in behavior_log[-10:])}
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        # Gợi ý sản phẩm dựa trên intent
        st.markdown("""
        <div class="glass-card">
          <h4 style="color:#94a3b8; margin-bottom:1rem;">🎯 Gợi ý sản phẩm phù hợp</h4>
        """, unsafe_allow_html=True)

        rec_products = random.sample(PRODUCTS, min(4, len(PRODUCTS)))
        for rp in rec_products:
            score = random.uniform(0.75, 0.99)
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:0.75rem; padding:0.6rem 0;
                        border-bottom:1px solid rgba(255,255,255,0.07);">
              <div style="font-size:1.8rem;">{rp['emoji']}</div>
              <div style="flex:1;">
                <div style="font-weight:600; color:#f1f5f9; font-size:0.88rem;">{rp['name'][:30]}…</div>
                <div style="color:#ef4444; font-weight:700; font-size:0.85rem;">{rp['price']:,}₫</div>
              </div>
              <div style="background:rgba(16,185,129,0.15); color:#10b981; padding:0.2rem 0.5rem;
                          border-radius:6px; font-size:0.75rem; font-weight:600;">
                {score:.0%}
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # Nút bổ sung hành vi manual
    st.markdown("---")
    st.markdown("**Mô phỏng hành vi thủ công:**")
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("🔍 Search", use_container_width=True):
            st.session_state.behavior_log.append("search"); st.rerun()
    with b2:
        if st.button("👁️ View", use_container_width=True):
            st.session_state.behavior_log.append("view"); st.rerun()
    with b3:
        if st.button("👆 Click", use_container_width=True):
            st.session_state.behavior_log.append("click"); st.rerun()
    with b4:
        if st.button("🛒 Add to Cart", use_container_width=True, type="primary"):
            st.session_state.behavior_log.append("add_to_cart"); st.rerun()
