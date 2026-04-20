"""
=============================================================
PHẦN 1 – Sinh tập dữ liệu hành vi người dùng
Môn: AI SERVICE
Output: data_user500.csv  +  in 20 dòng đầu dạng Markdown
=============================================================
Yêu cầu:
  - 500 users khác nhau (U001 … U500)
  - Cột: user_id, product_id, action (view/click/add_to_cart), timestamp
  - Mỗi user có nhiều hành vi → tổng cộng ~7 000 – 10 000 dòng
=============================================================
"""

import random
import math
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker

# ─── Cài faker nếu chưa có: pip install faker ───────────────
fake = Faker("vi_VN")
random.seed(42)

# ─── Hằng số ───────────────────────────────────────────────
N_USERS    = 500
N_PRODUCTS = 200          # 200 sản phẩm (P001 … P200)
ACTIONS    = ["view", "click", "add_to_cart"]
# Phân phối xác suất: view phổ biến hơn click, add_to_cart ít nhất
ACTION_WEIGHTS = [0.60, 0.28, 0.12]

START_DATE = datetime(2024, 1, 1)
END_DATE   = datetime(2025, 1, 1)
TOTAL_DAYS = (END_DATE - START_DATE).days

# Số hành vi mỗi user: phân phối Poisson, trung bình 17 → ~8 500 tổng
def _n_events_for_user() -> int:
    # Một số users rất tích cực (long tail)
    base = max(5, round(random.gauss(15, 8)))
    # ~5% users là "power users" với gấp đôi tương tác
    if random.random() < 0.05:
        base = int(base * 2.5)
    return base


# ─── Sinh dữ liệu ──────────────────────────────────────────
rows = []

for user_num in range(1, N_USERS + 1):
    user_id     = f"U{user_num:03d}"
    n_events    = _n_events_for_user()

    # Mỗi user có danh sách sản phẩm yêu thích (tăng tính thực tế)
    fav_products = random.sample(range(1, N_PRODUCTS + 1), k=min(10, N_PRODUCTS))

    # Sinh sự kiện tuần tự theo thời gian
    ts = START_DATE + timedelta(days=random.randint(0, TOTAL_DAYS - 1))

    for _ in range(n_events):
        # 60% khả năng chọn từ danh sách yêu thích
        if random.random() < 0.60:
            prod_num = random.choice(fav_products)
        else:
            prod_num = random.randint(1, N_PRODUCTS)

        product_id = f"P{prod_num:03d}"
        action     = random.choices(ACTIONS, weights=ACTION_WEIGHTS, k=1)[0]

        # Thêm khoảng cách ngẫu nhiên giữa các sự kiện (1 phút – 3 ngày)
        ts += timedelta(minutes=random.randint(1, 4320))
        # Không vượt quá END_DATE
        if ts > END_DATE:
            ts = END_DATE - timedelta(minutes=random.randint(1, 60))

        rows.append({
            "user_id":    user_id,
            "product_id": product_id,
            "action":     action,
            "timestamp":  ts.strftime("%Y-%m-%d %H:%M:%S"),
        })

# Sắp xếp theo timestamp
df = pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)

# ─── Lưu CSV ───────────────────────────────────────────────
OUTPUT_CSV = "data_user500.csv"
df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

print(f"✅ Đã tạo file: {OUTPUT_CSV}")
print(f"   Tổng số dòng  : {len(df):,}")
print(f"   Số users      : {df['user_id'].nunique()}")
print(f"   Số products   : {df['product_id'].nunique()}")
print(f"   Phân phối action:\n{df['action'].value_counts().to_string()}")
print()

# ─── In 20 dòng đầu dạng Markdown ─────────────────────────
print("## 20 dòng đầu tiên của tập dữ liệu `data_user500.csv`\n")
header = "| # | user_id | product_id | action | timestamp |"
sep    = "|---|---------|------------|--------|-----------|"
print(header)
print(sep)
for i, row in df.head(20).iterrows():
    print(f"| {i+1} | {row['user_id']} | {row['product_id']} | {row['action']} | {row['timestamp']} |")
