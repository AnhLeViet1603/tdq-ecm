# 📋 Hướng dẫn chạy – AI SERVICE Assignment

## Cấu trúc thư mục `services/ai/report/`

```
services/ai/report/
├── part1_generate_data.py     ← Phần 1: Sinh dữ liệu
├── part2_dl_models.py         ← Phần 2: RNN / LSTM / biLSTM
├── part3_neo4j_graph.py       ← Phần 3: Neo4j Knowledge Graph
├── part4_graph_rag.py         ← Phần 4: GraphRAG pipeline
├── part5_streamlit_app.py     ← Phần 5: UI Streamlit
└── README.md                  ← File này
```

---

## 🔷 Phần 1 – Sinh dữ liệu (Câu 1)

```bash
cd services/ai/report
pip install pandas faker
python part1_generate_data.py
```

**Output:** `data_user500.csv` (~8 000 dòng) + 20 dòng đầu dạng Markdown in ra terminal.

---

## 🔷 Phần 2 – 3 Mô hình Deep Learning (Câu 2a)

```bash
pip install torch pandas scikit-learn matplotlib seaborn
python part2_dl_models.py
```

**Output:**
- Biểu đồ so sánh: `report_plots/model_comparison.png`
- Trọng số model tốt nhất: `model_best.pth`
- Đánh giá chuyên sâu 3 mô hình in ra terminal

> ⚡ Nếu không có GPU, CPU chạy ~2-5 phút tùy máy.

---

## 🔷 Phần 3 – Neo4j Knowledge Graph (Câu 2b)

### Cài đặt Neo4j:
1. Tải [Neo4j Desktop](https://neo4j.com/download/) (miễn phí)
2. Tạo local database, đặt password
3. Start database

### Chạy script:
```bash
pip install neo4j pandas
# Cập nhật NEO4J_PASSWORD trong file part3_neo4j_graph.py
python part3_neo4j_graph.py
```

### Chụp ảnh đồ thị đẹp trong Neo4j Browser:
```cypher
MATCH (u:User)-[r]->(p:Product)
RETURN u, r, p LIMIT 100
```
- Tô màu **User** = xanh lam, **Product** = xanh lá
- Screenshot bằng `Win+Shift+S`

---

## 🔷 Phần 4 – GraphRAG (Câu 2c)

```bash
pip install neo4j google-generativeai
python part4_graph_rag.py
```

**Output:** Demo 5 câu hỏi ngôn ngữ tự nhiên + Cypher + câu trả lời tiếng Việt.

> Neo4j phải đang chạy. Nếu không, script sẽ báo lỗi kết nối.

---

## 🔷 Phần 5 – UI Streamlit (Câu 2d)

```bash
pip install streamlit google-generativeai neo4j pandas torch
streamlit run part5_streamlit_app.py
```

Mở trình duyệt tại: **http://localhost:8501**

### Các màn hình:
| Tab | Chức năng |
|-----|-----------|
| 🏠 Trang chủ | Danh sách sản phẩm, search, thêm giỏ hàng |
| 🤖 AI Chat | Chat với GraphRAG (Neo4j + Gemini) |
| 📊 Phân tích | Hành vi LSTM, intent prediction, gợi ý sản phẩm |

### Biến môi trường (tuỳ chọn):
```bash
set GEMINI_API_KEY=
set NEO4J_URI=bolt://localhost:7687
set NEO4J_USER=neo4j
set NEO4J_PASSWORD=your_password
```

---

## 📦 Cài đặt nhanh (tất cả)

```bash
pip install pandas faker torch scikit-learn matplotlib seaborn neo4j google-generativeai streamlit
```

---

## 🗂️ Tóm tắt Output cho Báo cáo

| Phần | Output cần chụp/copy |
|------|----------------------|
| Câu 1 | 20 dòng Markdown từ terminal |
| Câu 2a | `report_plots/model_comparison.png` + đoạn đánh giá từ terminal |
| Câu 2b | Screenshot Neo4j Browser graph + query Cypher 20 quan hệ |
| Câu 2c | Output terminal: Cypher + Answer cho 5 câu hỏi |
| Câu 2d | Screenshot Streamlit (3 tab) |
