# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Bùi Thu Trang
**Nhóm:** HUST
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Cosine similarity cao nghĩa là hai embedding gần cùng hướng, thường biểu diễn hai văn bản có ý nghĩa hoặc chủ đề gần nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: Người bán phải xin chấp thuận trước khi thu phí bổ sung.
- Câu B: Khách hàng phải đồng ý rõ ràng với khoản tiền cộng thêm.
- Tại sao tương đồng: Cả hai diễn đạt cùng điều kiện về explicit consent khi thanh toán.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Hàng lỗi được bảo hành tối thiểu hai năm.
- Câu B: Hôm nay trời nắng và ít mây.
- Tại sao khác: Một câu nói về chính sách thương mại, câu còn lại nói về thời tiết.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine tập trung vào hướng vector nên ít bị độ lớn của embedding chi phối; Euclid có thể tăng chỉ vì hai văn bản có độ dài khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* `ceil((10.000 - 50) / (500 - 50)) = ceil(22,11) = 23`.
> *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số chunk tăng thành `ceil((10.000 - 100) / 400) = 25`. Overlap lớn giữ ngữ cảnh ở biên tốt hơn nhưng tăng số embedding, dung lượng và nội dung trùng.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng `re.split(r"(?<=[.!?])\s+", text)`, strip và bỏ phần rỗng rồi gom tối đa số câu đã cấu hình. Text rỗng trả `[]`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thử separator từ đoạn đến ký tự, gom các phần vừa giới hạn và chia tiếp phần quá dài bằng separator thấp hơn. Base case là text đủ ngắn hoặc hết separator thì cắt cố định.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi Document thành record có id, content, bản sao metadata và embedding. Query chỉ embed một lần; store tính dot product, sort giảm dần và lấy top-k.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Filter metadata trước rồi mới rank để không bỏ mất ứng viên hợp lệ. Xóa tất cả chunk có `metadata['doc_id']` khớp và trả `True` khi kích thước giảm.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Agent retrieve top-k, đánh số chunk kèm doc_id, ghép Context/Question/Answer và yêu cầu chỉ trả lời từ context. Store rỗng trả thông báo mà không gọi LLM.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ python -m pytest tests -v
collected 42 items
tests/test_solution.py .......................................... [100%]
42 passed in 0.04s
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Faulty goods have a two-year guarantee. | Defective products are protected for two years. | cao | 0.1385 | Không rõ với mock |
| 2 | The seller needs consent for extra payment. | The merchant must obtain buyer approval for added fees. | cao | 0.0694 | Không rõ với mock |
| 3 | Can personalised goods be returned? | Tomorrow will be sunny. | thấp | -0.0289 | Có |
| 4 | The seller can repair or replace faulty goods. | Repair and replacement are remedies for defective products. | cao | 0.0609 | Không rõ với mock |
| 5 | A hosted gateway manages security updates. | This recipe uses rice and vegetables. | thấp | 0.0080 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Các cặp đồng nghĩa vẫn có điểm thấp vì MockEmbedder hash chuỗi chứ không hiểu ý nghĩa. Kết quả này chỉ kiểm tra phép tính và pipeline; benchmark semantic cần local embedding.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

Lệnh: `python bench.py`. Strategy: `HeadingChunker(chunk_size=500)`, 17 chunks, mock embedding.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | How long is the minimum legal guarantee for faulty goods? | Total price — `eu-pricing-payments::chunk_0` | 0.1383 | Không | Context thiếu số liệu bảo hành |
| 2 | When can a buyer receive a refund instead of repair or replacement? | Legal guarantee — `eu-guarantees-returns::chunk_0` | 0.1115 | Có, top-1 | Context chứa đủ điều kiện hoàn tiền |
| 3 | What must an online seller do before charging an extra payment at checkout? | Cross-border payment setup — `eu-online-shop-rules::chunk_1` | 0.2025 | Có, top-3 | Context top-3 chứa explicit consent |
| 4 | Which product problems allow a customer to claim redress from a seller? | After-payment duties — `eu-online-shop-rules::chunk_3` | 0.1961 | Không | Không có danh sách redress |
| 5 | Can an online customer return clearly personalised goods during the cooling-off period? | Card fees — `eu-pricing-payments::chunk_1` | 0.1600 | Có, top-2 | Context top-2 chứa ngoại lệ personalised goods |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 3 / 5

**Failure case:** Query 4 trả các chunk payment dù gold nằm ở mục redress. Heading được giữ đúng nhưng MockEmbedder không hiểu ngữ nghĩa, nên chunk coherence tốt không tự bảo đảm ranking đúng; cần chạy lại cùng query bằng local embedding.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> SentenceChunker thắng query số liệu, còn RecursiveChunker(350) đưa checkout process lên top-1. Strategy theo heading giữ section tốt nhất nhưng vẫn phụ thuộc embedder khi xếp hạng.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 4 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 4 / 10 |
| **Tổng phần cá nhân** | **52 / 60** |
