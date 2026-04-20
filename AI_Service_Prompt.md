# Prompt Bài Tập AI SERVICE

**Vai trò của bạn:** Bạn là một AI Engineer và Full-stack Developer xuất sắc. Hãy giúp tôi hoàn thành bài tập môn "AI SERVICE" với các yêu cầu lập trình và viết báo cáo chi tiết. Hãy viết code bằng Python và cung cấp các lời giải thích rõ ràng để tôi có thể tổng hợp thành file PDF báo cáo.

**Bối cảnh:** Bài tập yêu cầu xây dựng toàn bộ luồng từ tạo dữ liệu giả, huấn luyện mô hình Deep Learning (RNN, LSTM, biLSTM), xây dựng Knowledge Graph bằng Neo4j, tạo hệ thống RAG trên Graph và cuối cùng là demo UI tích hợp.

Hãy thực hiện tuần tự các yêu cầu sau và trình bày thật rõ ràng, chia làm các mục dễ copy:

**Phần 1: Sinh tập dữ liệu (Tương ứng Câu 1)**
Viết script Python (dùng `pandas`, `random`, `faker`) để tạo file `data_user500.csv` thỏa mãn:
- Có 500 users khác nhau.
- Các cột: `user_id`, `product_id`, `action` (view, click, add_to_cart), `timestamp`.
- Tạo logic sao cho mỗi user có nhiều hành vi (tổng cộng khoảng vài ngàn dòng). 
- **Output:** Cung cấp code sinh dữ liệu và in ra màn hình dạng bảng Markdown **20 dòng đầu tiên** của tập data này để tôi đưa vào báo cáo.

**Phần 2: Xây dựng mô hình Deep Learning (Tương ứng Câu 2a)**
Sử dụng PyTorch hoặc TensorFlow/Keras để thực hiện phân loại hành vi người dùng (Classification) hoặc dự đoán hành vi tiếp theo dựa trên tập dữ liệu trên.
- Viết code xây dựng 3 mô hình: **RNN, LSTM, và biLSTM**.
- Viết code huấn luyện, tính toán các độ đo (Accuracy, F1-Score, Loss).
- Viết code dùng `matplotlib` hoặc `seaborn` để vẽ biểu đồ so sánh kết quả (Loss curve, Accuracy bar chart) của 3 mô hình.
- **Output:** Cung cấp toàn bộ code. Đặc biệt, hãy viết **một đoạn đánh giá chuyên sâu (bằng lời)** phân tích ưu nhược điểm của 3 mô hình trên tập data này và chọn ra mô hình tốt nhất (`model_best`).

**Phần 3: Knowledge Base Graph với Neo4j (Tương ứng Câu 2b)**
- Viết script Python kết nối với Neo4j (sử dụng thư viện `neo4j`).
- Viết các câu lệnh Cypher để import file CSV vừa tạo vào Neo4j, tạo các Node: `User`, `Product` và các Relationship: `VIEWED`, `CLICKED`, `ADDED_TO_CART` cùng thuộc tính `timestamp`.
- **Output:** Code Python thực thi việc này và cung cấp **một đoạn query Cypher** để trích xuất 20 dòng quan hệ phức tạp, kèm hướng dẫn cách chụp ảnh graph đẹp trên giao diện Neo4j Browser.

**Phần 4: Hệ thống RAG và Chat trên KB_Graph (Tương ứng Câu 2c)**
- Viết script Python sử dụng LangChain hoặc LlamaIndex kết hợp với LLM (ví dụ OpenAI API hoặc mô hình mã nguồn mở) để xây dựng hệ thống **GraphRAG**.
(Có sẵn gemini key api : AIzaSyDxqxtaY0j34jqfhbPLtCA38Ws07l5q45k)
- Hệ thống phải có khả năng nhận câu hỏi bằng ngôn ngữ tự nhiên (VD: "User U001 đã click vào những sản phẩm nào?"), chuyển thành Cypher query, truy xuất Neo4j và sinh ra câu trả lời.
- **Output:** Code hoàn chỉnh cho hệ thống RAG và đoạn tài liệu ngắn (khoảng 300 chữ) giải thích cơ chế hoạt động của GraphRAG trong dự án này.

**Phần 5: Triển khai UI E-commerce (Tương ứng Câu 2d)**
Viết một ứng dụng Web đơn giản bằng **Streamlit** (hoặc HTML/JS/Flask tùy bạn chọn, nhưng Streamlit là nhanh nhất để demo AI) để tích hợp các phần trên:
- Có một màn hình hiển thị danh sách sản phẩm khi người dùng search hoặc click "Thêm vào giỏ hàng".
- Tích hợp một **Giao diện Chat** (Custom Chat UI, không dùng UI mặc định của ChatGPT) để người dùng có thể chat và hỏi thông tin, kết nối trực tiếp với backend GraphRAG ở Câu 2c.
- **Output:** Cung cấp code UI và hướng dẫn cách chạy ứng dụng để tôi có thể chụp màn hình giao diện.

***

### 💡 Lời khuyên thêm cho bạn:
1. **Chạy từng phần:** Vì bài khá dài, nếu AI bị ngắt quãng giữa chừng, bạn hãy nhắn "Viết tiếp phần [Tên phần đang viết dở]" để AI hoàn thiện.
2. **Hình ảnh (`.png`, `.jpg`):** AI có thể viết code tạo biểu đồ (matplotlib), nhưng bạn **phải tự chạy file Python đó trên máy tính của bạn** (dùng Google Colab, VS Code, hoặc Jupyter Notebook) để lấy được ảnh đồ thị (plots) và giao diện chụp cho vào file PDF nhé.
3. **Neo4j:** Đối với câu 2b yêu cầu "ảnh càng phức tạp-đẹp càng có giá trị", bạn nên tải Neo4j Desktop, chạy code import, sau đó dùng query: `MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 100` rồi tùy chỉnh màu sắc các node trên giao diện Neo4j Browser để chụp ảnh màn hình cho đẹp. Chúc bạn làm đồ án đạt điểm cao!
