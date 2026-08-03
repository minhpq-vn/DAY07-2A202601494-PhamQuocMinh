# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** HUST
**Thành viên:** Phạm Quốc Minh - 2A202601494, Phạm Danh Tuấn Dũng - 2A202601978, Đinh Việt Anh - 2A202601516, Bùi Thu Trang - 2A202601758, Phan Trọng Đạt - 2A202601138
**Ngày:** 2026-08-03

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Chính sách mua sắm trực tuyến tại EU: quyền đổi trả, giá/thanh toán của người mua và nghĩa vụ bảo hành/payment setup của người bán.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Guarantees and returns | https://europa.eu/youreurope/citizens/consumers/shopping/guarantees/index_en.htm | 2026-08-03 / 2026-07-30 | 1,580 | buyer, returns, en |
| 2 | Consumer shopping rights | https://europa.eu/youreurope/citizens/consumers/shopping/shopping-consumer-rights/index_en.htm | 2026-08-03 / 2025-09-25 | 1,389 | buyer, buyer-rights, en |
| 3 | Pricing and payments | https://europa.eu/youreurope/citizens/consumers/shopping/pricing-payments/index_en.htm | 2026-08-03 / 2025-06-16 | 1,551 | buyer, pricing-payments, en |
| 4 | Seller guarantees | https://europa.eu/youreurope/business/selling-in-eu/consumer-contracts-guarantees/consumer-guarantees/index_en.htm | 2026-08-03 / 2026-07-12 | 1,567 | seller, guarantees, en |
| 5 | Online-shop payment rules | https://europa.eu/youreurope/business/growing/digitalising/setting-up-online-shop/index_en.htm | 2026-08-03 / 2026-07-13 | 1,517 | seller, online-shop, en |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| doc_id | string | eu-shopping-rights | Nối chunk về tài liệu gốc và hỗ trợ xóa |
| title | string | Consumer shopping rights in the EU | Hiển thị và truy vết tài liệu |
| source_url | URL string | https://europa.eu/... | Kiểm chứng gold answer |
| retrieved_at | ISO date | 2026-08-03 | Minh bạch thời điểm thu thập |
| document_version | ISO date | 2025-09-25 | Theo dõi phiên bản nguồn |
| customer_role | enum | buyer / seller | Filter bắt buộc của K4 |
| category | string | pricing-payments | Thu hẹp chủ đề policy |
| language | ISO code | en | Chọn query và embedding phù hợp |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| eu-guarantees-returns | FixedSizeChunker (`fixed_size`) | 3 | 428.0 | Có thể cắt giữa câu |
| eu-guarantees-returns | SentenceChunker (`by_sentences`) | 4 | 319.5 | Có, giữ câu hoàn chỉnh |
| eu-guarantees-returns | RecursiveChunker (`recursive`) | 4 | 319.5 | Có, ưu tiên heading/đoạn |
| eu-pricing-payments | FixedSizeChunker (`fixed_size`) | 3 | 416.7 | Có thể cắt giữa câu |
| eu-pricing-payments | SentenceChunker (`by_sentences`) | 4 | 311.0 | Có, giữ câu hoàn chỉnh |
| eu-pricing-payments | RecursiveChunker (`recursive`) | 3 | 415.3 | Có, giữ ranh giới tự nhiên |
| eu-seller-guarantees | FixedSizeChunker (`fixed_size`) | 3 | 412.3 | Có thể cắt ý redress |
| eu-seller-guarantees | SentenceChunker (`by_sentences`) | 3 | 411.0 | Có, giữ câu hoàn chỉnh |
| eu-seller-guarantees | RecursiveChunker (`recursive`) | 3 | 411.0 | Có, cân bằng kích thước/ngữ cảnh |

Các số trên dùng `load_documents()` nên chỉ đo body; YAML front matter đã được bỏ trước khi comparator chạy.

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Phạm Quốc Minh**
- **Loại chiến lược:** RecursiveChunker (`chunk_size=400`)
- **Mô tả & lý do chọn cho chủ đề này:** Corpus có heading và đoạn policy rõ ràng. Recursive ưu tiên ranh giới tự nhiên nhưng vẫn fallback xuống từ/ký tự nếu một phần vượt giới hạn.
- **Code snippet (nếu custom):**
```python
# Không dùng custom chunker.
```

**Thành viên 2 — Phạm Danh Tuấn Dũng**
- **Loại chiến lược:** FixedSizeChunker (`chunk_size=450`, `overlap=50`)
- **Mô tả & lý do chọn:** Baseline đơn giản, có overlap để một thông tin ở biên có thêm cơ hội xuất hiện trong retrieval.
- **Code snippet (nếu custom):** Không dùng custom chunker.

**Thành viên 3 — Đinh Việt Anh**
- **Loại chiến lược:** SentenceChunker (`max_sentences_per_chunk=3`)
- **Mô tả & lý do chọn:** Không cắt giữa câu, phù hợp với câu policy chứa đủ điều kiện và kết quả.
- **Code snippet (nếu custom):** Không dùng custom chunker.

**Thành viên 4 — Bùi Thu Trang**
- **Loại chiến lược:** HeadingChunker (`chunk_size=500`)
- **Mô tả & lý do chọn:** Mỗi mục Markdown là một đơn vị policy; section dài được RecursiveChunker cắt tiếp và gắn lại heading vào mọi mảnh con.
- **Code snippet (nếu custom):** Xem `HeadingChunker` trong `bench.py`.

**Thành viên 5 — Phan Trọng Đạt**
- **Loại chiến lược:** RecursiveChunker (`chunk_size=350`)
- **Mô tả & lý do chọn:** Chunk nhỏ hơn strategy của Minh để đo đánh đổi giữa độ tập trung thông tin và mất ngữ cảnh.
- **Code snippet (nếu custom):** Không dùng custom chunker.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Phạm Quốc Minh | RecursiveChunker(400) — 21 chunks | 3/10 | Giữ đoạn, Q2/Q3/Q5 có evidence | Có chunk chỉ chứa heading; Q1/Q4 fail |
| Phạm Danh Tuấn Dũng | FixedSize(450, overlap=50) — 16 chunks | 0/10 | Ít chunk, có overlap | Cắt giữa từ/câu; không marker nào vào top-3 |
| Đinh Việt Anh | SentenceChunker(3) — 18 chunks | 4/10 | Q1 evidence ở top-1, câu hoàn chỉnh | Q2/Q4 fail; độ dài không bị chặn tuyệt đối |
| Bùi Thu Trang | HeadingChunker(500) — 17 chunks | 4/10 | Q2 top-1; giữ heading trên sub-chunk | Q1/Q4 fail do ranking mock |
| Phan Trọng Đạt | RecursiveChunker(350) — 26 chunks | 3/10 | Q3 evidence ở top-1 | Nhiều chunk vụn; Q1/Q2/Q4 fail |

Output thật khi chạy `python bench.py` trong từng thư mục thành viên:

```text
Embedding backend: mock embeddings fallback
minh_recursive_400: 3/10
dung_fixed_450_overlap_50: 0/10
vietanh_sentence_3: 4/10
trang_heading_500: 4/10
dat_recursive_350: 3/10
```

Mỗi thư mục thành viên chứa độc lập `src/`, `tests/`, corpus chung, `ingest.py`, `bench.py` và `report/REPORT_CANHAN.md`. Năm file `bench.py` dùng cùng query, gold answer, filter, mock embedder và runner; dòng chọn chunker là phần khác nhau.

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> SentenceChunker và HeadingChunker cùng đạt 4/10 với mock. Nhóm chọn HeadingChunker cho demo vì nó khớp cấu trúc policy và không làm mất tên mục khi section dài; chưa thể kết luận chất lượng semantic cho tới khi chạy local embedding.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 — số liệu | How long is the minimum legal guarantee for faulty goods? | Two years from receipt of the goods. | `eu-guarantees-returns`; marker `minimum legal guarantee lasts two years`; filter buyer |
| 2 — điều kiện | When can a buyer receive a refund instead of repair or replacement? | When repair or replacement is impossible or cannot be completed reasonably without significant inconvenience. | `eu-guarantees-returns`; marker `within a reasonable time and without significant inconvenience`; filter buyer |
| 3 — quy trình | What must an online seller do before charging an extra payment at checkout? | Disclose accepted methods and total costs, then obtain explicit consent for the extra payment. | `eu-online-shop-rules`; marker `extra payments require explicit customer consent`; filter seller |
| 4 — liệt kê | Which product problems allow a customer to claim redress from a seller? | Mismatch with description or advertising, unfitness for purpose, abnormal quality/performance, or incorrect installation. | `eu-seller-guarantees`; marker `does not match its description`; filter seller |
| 5 — ngoại lệ | Can an online customer return clearly personalised goods during the cooling-off period? | No. Clearly personalised goods are exempt from the general fourteen-day cooling-off period. | `eu-shopping-rights`; marker `personalised goods`; filter buyer |

Năm query, gold answer, marker và filter trên được khóa trong `bench.py`; mọi thành viên dùng cùng embedder `_mock_embed`, chỉ đổi strategy.

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Minimum legal guarantee | SentenceChunker(3) | Có, top-1 | Marker số liệu nằm trong chunk hoàn chỉnh |
| 2 | Refund conditions | HeadingChunker(500) | Có, top-1 | Heading và điều kiện/ngoại lệ cùng chunk |
| 3 | Extra payment process | RecursiveChunker(350) | Có, top-1 | Filter seller đưa đúng checkout chunk lên đầu |
| 4 | Redress problem list | Không strategy nào | Không | Đúng doc có thể đứng top-1 nhưng sai section |
| 5 | Personalised-goods exception | HeadingChunker(500) | Có, top-2 | Section giữ cả quy tắc 14 ngày và ngoại lệ |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có rõ nhất ở câu 2, 3 và 5: Heading Q2 đổi evidence từ top-2 lên top-1; Recursive(350) Q3 từ không có evidence thành top-1; Heading Q5 từ top-3 lên top-2. Filter giảm nhiễu nhưng không cứu được câu 4, nên metadata không thay thế semantic ranking.

**Failure case có bằng chứng:** Với query 4 của Minh, top-1 là `eu-seller-guarantees::chunk_3` nhưng chỉ chứa heading “Available remedies”; top-2 cũng cùng gold `doc_id` nhưng không chứa marker “does not match its description”. Đây là trường hợp chấm doc-level báo đúng nhưng chunk-level phải là 0. Nguyên nhân gồm heading bị tách riêng và mock embedding không hiểu truy vấn; đề xuất dùng HeadingChunker để gắn lại tiêu đề và chạy local embedding.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> Sentence thắng query số liệu; Heading thắng query điều kiện và giữ tên mục; doc_id đúng không đủ nếu chunk thiếu marker gold; metadata filter phải chạy trước ranking.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng corpus/query/embedder nhưng năm strategy tạo 16–26 chunks và điểm 0–4/10. FixedSize cắt evidence ở biên, Recursive nhỏ tạo nhiều mảnh, còn Sentence/Heading giữ đơn vị ngữ nghĩa tốt hơn; mock vẫn không đủ để kết luận retrieval semantic.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Giữ nguyên corpus, gold answer và 5 query đã khóa; chạy semantic embedding rồi chỉ tune chunk size/overlap, không đổi query theo kết quả.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 7 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **37 / 40** |
