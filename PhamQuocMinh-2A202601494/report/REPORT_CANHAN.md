# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phạm Quốc Minh
**Nhóm:** HUST
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector gần cùng hướng, nên embedding xem hai đoạn có nội dung hoặc ngữ nghĩa gần nhau dù độ dài có thể khác.

**Ví dụ có độ tương tự CAO:**
- Câu A: Người mua được hoàn tiền khi hàng bị lỗi.
- Câu B: Khách hàng có thể nhận lại tiền cho sản phẩm khiếm khuyết.
- Tại sao tương đồng: Hai câu dùng từ khác nhưng cùng nói về quyền hoàn tiền cho hàng lỗi.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Người bán phải công khai tổng giá.
- Câu B: Ngày mai trời có mưa.
- Tại sao khác: Hai câu thuộc hai chủ đề không liên quan.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine so hướng vector và ít bị độ lớn hoặc độ dài văn bản chi phối; Euclid có thể coi hai vector cùng hướng nhưng khác độ lớn là xa nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* `ceil((10.000 - 50) / (500 - 50)) = ceil(9.950 / 450) = 23`.
> *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số chunk tăng thành `ceil((10.000 - 100) / 400) = 25`. Overlap lớn giữ thêm ngữ cảnh ở biên nhưng tăng chi phí embedding, lưu trữ và nội dung trùng lặp.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng `re.split(r"(?<=[.!?])\s+", text)` để tách tại khoảng trắng sau dấu kết câu và giữ dấu câu ở phần trước. Text rỗng trả `[]`; các phần được strip, bỏ rỗng và ghép theo giới hạn số câu.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Ưu tiên ranh giới đoạn, dòng, câu rồi từ. Base case trả nguyên text khi đủ ngắn; nếu hết separator hoặc gặp separator rỗng thì cắt cố định. Mỗi lần đệ quy đều bỏ separator hiện tại nên luôn tiến tới điều kiện dừng.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Chuẩn hóa mỗi Document thành record gồm id duy nhất, content, bản sao metadata và embedding. Search tạo query embedding một lần, tính dot product, sắp xếp giảm dần rồi lấy top-k.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc metadata trước khi rank để không mất ứng viên hợp lệ. Xóa tất cả chunk có cùng `metadata['doc_id']` và trả về việc số record có giảm hay không.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Retrieve top-k, đánh số chunk kèm `doc_id`, rồi tạo prompt gồm chỉ dẫn chỉ dùng context, Context, Question và Answer. Store rỗng trả thông báo rõ ràng mà không gọi LLM.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ .venv/bin/python -m pytest tests -v
============================= test session starts ==============================
collected 42 items
tests/test_solution.py ..........................................          [100%]
============================== 42 passed in 0.04s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | A buyer can return a faulty item. | A customer may seek a remedy for defective goods. | cao | -0.2019 | Không |
| 2 | Online orders have a cancellation period. | Tomorrow will be rainy and cold. | thấp | -0.1485 | Có |
| 3 | The seller must disclose the total price. | A merchant must show every fee before checkout. | cao | 0.0402 | Không rõ |
| 4 | A hosted payment gateway manages security updates. | This soup recipe uses carrots and onions. | thấp | 0.0904 | Không |
| 5 | The trader must repair or replace faulty goods. | Defective products may qualify for repair or replacement. | cao | -0.0420 | Không |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Các cặp đồng nghĩa có thể nhận điểm âm vì `_mock_embed` chỉ tạo vector xác định để test pipeline, không biểu diễn ngữ nghĩa. Benchmark chất lượng cần dùng embedding local hoặc API thật.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

Lệnh: `python bench.py`. Strategy: `RecursiveChunker(chunk_size=400)`, 21 chunks, mock embedding.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | How long is the minimum legal guarantee for faulty goods? | Seller status trong `eu-shopping-rights::chunk_0` | 0.1465 | Không, không có evidence trong top-3 | Không đủ context để trả lời số liệu |
| 2 | When can a buyer receive a refund instead of repair or replacement? | Additional services trong `eu-pricing-payments::chunk_1` | 0.1167 | Có ở top-2 | Context top-2 chứa điều kiện hoàn tiền |
| 3 | What must an online seller do before charging an extra payment at checkout? | Withdrawal trong `eu-seller-guarantees::chunk_0` | 0.1910 | Có ở top-2 | Context top-2 chứa yêu cầu explicit consent |
| 4 | Which product problems allow a customer to claim redress from a seller? | Heading rỗng ý `Available remedies` trong `eu-seller-guarantees::chunk_3` | 0.2583 | Không, đúng doc nhưng sai section | Không có danh sách điều kiện redress |
| 5 | Can an online customer return clearly personalised goods during the cooling-off period? | Legal guarantee trong `eu-guarantees-returns::chunk_0` | 0.2638 | Có ở top-2 | Context top-2 chứa ngoại lệ personalised goods |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 3 / 5

**Failure case có bằng chứng:** Query 4 trả `eu-seller-guarantees::chunk_3` ở top-1 nhưng chunk chỉ có heading “Available remedies”; top-2 cũng đúng `doc_id` nhưng không chứa chuỗi gold “does not match its description”. Vì vậy chấm theo `doc_id` sẽ báo đúng giả, còn chấm evidence-level là 0. Nguyên nhân là mock embedding xếp hạng ngẫu nhiên theo ngữ nghĩa và RecursiveChunker có thể tạo heading đứng riêng; đề xuất dùng local embedding và heading-aware chunker để gắn lại tiêu đề vào từng mảnh.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> SentenceChunker đưa câu hỏi số liệu lên top-1, còn heading-aware giữ tên section trên mọi sub-chunk. Tuy nhiên cả hai vẫn có failure khi dùng mock, cho thấy chunk coherence và semantic ranking là hai vấn đề độc lập.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 4 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 3 / 10 |
| **Tổng phần cá nhân** | **51 / 60** |
