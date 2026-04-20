"""
=============================================================
PHẦN 3 – Knowledge Base Graph với Neo4j
Môn: AI SERVICE
=============================================================
Yêu cầu pip: pip install neo4j pandas

Trước khi chạy:
  1. Cài Neo4j Desktop hoặc dùng Neo4j AuraDB miễn phí
  2. Tạo database, ghi lại URI / user / password
  3. Cập nhật NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD bên dưới
  4. Copy file data_user500.csv vào thư mục import của Neo4j
     (chỉ cần nếu dùng LOAD CSV qua đường dẫn neo4j:///)
     Hoặc dùng đường dẫn file:// tuyệt đối như hướng dẫn bên dưới
=============================================================
"""

import csv
import time
from datetime import datetime
from neo4j import GraphDatabase

# ─── CẤU HÌNH KẾT NỐI ───────────────────────────────────────
NEO4J_URI      = "neo4j://127.0.0.1:7687"    # Đổi nếu dùng AuraDB
NEO4J_USER     = "neo4j"
NEO4J_PASSWORD = "admin123"      # <-- Đổi thành mật khẩu của bạn
CSV_PATH       = "data_user500.csv"        # Đường dẫn tương đối hoặc tuyệt đối

BATCH_SIZE     = 500   # Import theo batch để tránh quá tải bộ nhớ


# ════════════════════════════════════════════════════════════
# 1. Kết nối Neo4j
# ════════════════════════════════════════════════════════════
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def run_query(tx, query, **params):
    return list(tx.run(query, **params))

def run(query, **params):
    with driver.session() as session:
        return session.execute_write(run_query, query, **params)

def run_read(query, **params):
    with driver.session() as session:
        return session.execute_read(run_query, query, **params)


# ════════════════════════════════════════════════════════════
# 2. Xoá dữ liệu cũ & tạo Index / Constraint
# ════════════════════════════════════════════════════════════
print("▶ Thiết lập schema Neo4j …")

setup_queries = [
    # Xoá toàn bộ graph (chỉ dùng khi development)
    "MATCH (n) DETACH DELETE n",

    # Unique constraint
    "CREATE CONSTRAINT IF NOT EXISTS FOR (u:User)    REQUIRE u.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE",

    # Index tăng tốc lookup
    "CREATE INDEX IF NOT EXISTS FOR (u:User)    ON (u.id)",
    "CREATE INDEX IF NOT EXISTS FOR (p:Product) ON (p.id)",
]

for q in setup_queries:
    try:
        run(q)
        print(f"  ✅ {q[:60]}…")
    except Exception as e:
        print(f"  ⚠️  {e}")

print()


# ════════════════════════════════════════════════════════════
# 3. Đọc CSV & Import theo Batch
# ════════════════════════════════════════════════════════════
print("▶ Đọc CSV …")
rows = []
with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)
print(f"  Tổng số dòng: {len(rows):,}")

# Map hành vi → kiểu relationship trong Neo4j
ACTION_MAP = {
    "view":        "VIEWED",
    "click":       "CLICKED",
    "add_to_cart": "ADDED_TO_CART",
}


def import_batch(tx, batch):
    """
    Với mỗi hành vi trong batch:
      - MERGE User node
      - MERGE Product node
      - CREATE relationship tương ứng kèm timestamp
    """
    for row in batch:
        rel_type = ACTION_MAP.get(row["action"], "INTERACTED")
        cypher = f"""
        MERGE (u:User    {{id: $uid}})
        MERGE (p:Product {{id: $pid}})
        CREATE (u)-[:{rel_type} {{timestamp: $ts}}]->(p)
        """
        tx.run(cypher, uid=row["user_id"], pid=row["product_id"], ts=row["timestamp"])


print("▶ Import dữ liệu vào Neo4j …")
t0 = time.time()
with driver.session() as session:
    for start in range(0, len(rows), BATCH_SIZE):
        batch = rows[start:start + BATCH_SIZE]
        session.execute_write(import_batch, batch)
        print(f"  Imported {min(start+BATCH_SIZE, len(rows)):,} / {len(rows):,} rows …")

elapsed = time.time() - t0
print(f"✅ Import hoàn tất trong {elapsed:.1f}s\n")


# ════════════════════════════════════════════════════════════
# 4. Kiểm tra – truy vấn thống kê
# ════════════════════════════════════════════════════════════
stats_queries = {
    "Số User nodes":         "MATCH (u:User)    RETURN count(u) AS cnt",
    "Số Product nodes":      "MATCH (p:Product) RETURN count(p) AS cnt",
    "Số VIEWED":             "MATCH ()-[r:VIEWED]->()        RETURN count(r) AS cnt",
    "Số CLICKED":            "MATCH ()-[r:CLICKED]->()       RETURN count(r) AS cnt",
    "Số ADDED_TO_CART":      "MATCH ()-[r:ADDED_TO_CART]->() RETURN count(r) AS cnt",
}

print("▶ Thống kê graph:")
for label, q in stats_queries.items():
    result = run_read(q)
    print(f"  {label:25s}: {result[0]['cnt']:,}")

print()


# ════════════════════════════════════════════════════════════
# 5. Query Cypher trích xuất 20 quan hệ phức tạp
#    (Copy câu này vào Neo4j Browser để chụp ảnh graph)
# ════════════════════════════════════════════════════════════
COMPLEX_QUERY = """
// ─── TRÍCH XUẤT 20 QUAN HỆ PHỨC TẠP ────────────────────────────────────────
// Mục tiêu: Lấy những User đã tương tác ít nhất 2 loại hành vi khác nhau
//            với cùng một Product → biểu thị "quan tâm nhiều chiều"
// ─────────────────────────────────────────────────────────────────────────────

MATCH (u:User)-[r1:VIEWED]->(p:Product)<-[r2:CLICKED]-(u)
WHERE r1.timestamp < r2.timestamp

OPTIONAL MATCH (u)-[r3:ADDED_TO_CART]->(p)

WITH u, p,
     r1.timestamp AS view_ts,
     r2.timestamp AS click_ts,
     r3.timestamp AS cart_ts

RETURN
    u.id AS user_id,
    p.id AS product_id,
    view_ts,
    click_ts,
    cart_ts,
    CASE 
        WHEN cart_ts IS NOT NULL THEN 'view→click→cart' 
        ELSE 'view→click' 
    END AS funnel
ORDER BY user_id, product_id
LIMIT 20
"""

print("─" * 70)
print("CYPHER QUERY – Dùng trong Neo4j Browser để chụp ảnh đồ thị phức tạp:")
print("─" * 70)
print(COMPLEX_QUERY)

print()
print("─" * 70)
print("CYPHER QUERY – Visualize toàn bộ đồ thị (dùng để chụp ảnh đẹp):")
print("─" * 70)
VISUAL_QUERY = """
MATCH (u:User)-[r]->(p:Product)
WITH u, r, p, type(r) AS rel_type
ORDER BY u.id, p.id
LIMIT 100
RETURN u, r, p
"""
print(VISUAL_QUERY)

print()
print("💡 Hướng dẫn chụp ảnh graph đẹp trên Neo4j Browser:")
print("""
  1. Mở Neo4j Desktop → Start database → Open Neo4j Browser
  2. Paste query VISUAL_QUERY ở trên → nhấn Run (▶)
  3. Click nút 'Graph' (icon mạng) trong phần kết quả
  4. Tùy chỉnh màu sắc:
     - Click vào node User → chọn màu xanh lam (#3b82f6)
     - Click vào node Product → chọn màu xanh lá (#10b981)
  5. Điều chỉnh layout: chọn 'Force' hoặc 'Hierarchical'
  6. Phóng to vùng quan tâm, chụp màn hình (Win+Shift+S)
  Gợi ý: dùng query LIMIT 50-100 để đồ thị không bị rối
""")

# ── Đóng kết nối ────────────────────────────────────────────
driver.close()
print("✅ Kết nối Neo4j đã đóng.")
