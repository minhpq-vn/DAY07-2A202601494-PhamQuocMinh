# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phạm Danh Tuấn Dũng
**Nhóm:** HUST
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm nằm trong `REPORT_NHOM.md` và thang điểm nằm trong `docs/SCORING.md` ở thư mục gốc repo nhóm.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai đoạn văn bản có độ tương tự cosine cao (tiệm cận 1.0) nghĩa là hai vector biểu diễn (embeddings) của chúng chỉ về cùng một hướng trong không gian đa chiều, thể hiện sự tương đồng cao về mặt ý nghĩa ngữ nghĩa và chủ đề.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Tôi muốn làm thủ tục hoàn trả sản phẩm bị hư hỏng."
- Câu B: "Hướng dẫn quy trình trả lại hàng hóa bị lỗi cho khách hàng."
- Tại sao tương đồng: Cả hai câu đều xoay quanh cùng một chủ đề (yêu cầu/quy trình trả hàng bị lỗi) dù cách dùng từ khác nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Chính sách đổi trả hàng áp dụng trong vòng 7 ngày."
- Câu B: "Thời tiết Hà Nội hôm nay nhiều mây và có mưa rào."
- Tại sao khác: Hai câu thuộc hai ngữ cảnh hoàn toàn không liên quan tới nhau (quy định mua bán vs dự báo thời tiết).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid bị phụ thuộc vào độ dài (độ lớn magnitude) của vector, khiến hai văn bản cùng nội dung nhưng khác độ dài có thể nằm xa nhau. Cosine similarity chỉ đo góc giữa hai vector (hướng ngữ nghĩa), loại bỏ ảnh hưởng của độ dài văn bản nên phản ánh độ tương đồng ngữ nghĩa chính xác hơn.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* $\text{Số chunk} = \left\lceil \frac{10000 - 50}{500 - 50} \right\rceil = \left\lceil \frac{9950}{450} \right\rceil = \left\lceil 22.11 \right\rceil = 23$
> *Đáp án:* 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Trình bày phép tính:* Khi overlap = 100, $\text{Số chunk} = \left\lceil \frac{10000 - 100}{500 - 100} \right\rceil = \left\lceil \frac{9900}{400} \right\rceil = \left\lceil 24.75 \right\rceil = 25$ chunks (tăng từ 23 lên 25 chunks).
> *Lý do:* Tăng độ chồng chéo giúp đảm bảo ngữ cảnh tại các ranh giới phân chia không bị mất hoặc ngắt đứt đột ngột, giúp thông tin nằm ở giáp ranh giữa hai chunk vẫn được giữ trọn vẹn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng regex `re.split(r'(?<=[.!?])\s+', text)` để tách văn bản thành danh sách các câu dựa trên dấu chấm, hỏi, cảm thán. Gom tối đa `max_sentences` câu vào mỗi chunk, dùng string join với khoảng trắng để nối lại.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy cắt văn bản dựa theo danh sách phân cách ưu tiên từ lớn đến nhỏ (`["\n\n", "\n", ". ", " "]`). Nếu kích thước đoạn văn bản vẫn lớn hơn `chunk_size`, hàm đệ quy thử phân cách kế tiếp; trường hợp cơ sở là kích thước đoạn nhỏ hơn hoặc bằng `chunk_size` hoặc đã hết danh sách phân cách thì cắt cứng theo ký tự.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` tạo dict record gồm `id`, `content`, bản sao `metadata` (chứa `doc_id`), và vector `embedding` từ `_embedding_fn`. Khi `search`, tính dot product của query embedding với vector từng record qua helper `_search_records`, sau đó sắp xếp giảm dần theo điểm `score` và lấy `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc (filter) trước khi rank: duyệt qua danh sách lưu trữ `_store` để chọn các record thỏa mãn toàn bộ cặp key-value trong `metadata_filter`, rồi mới chuyển các candidate này vào `_search_records`. `delete_document` loại bỏ tất cả record có `metadata['doc_id']` hoặc `id` trùng với `doc_id` của tài liệu gốc.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Gọi `self.store.search(question, top_k)` để lấy danh sách chunk liên quan. Đánh số từng chunk `[1]`, `[2]`, ... kèm thông tin nguồn `Nguồn: <source/doc_id>` để đảm bảo tính grounding và dễ truy vết. Inject context vào prompt cùng instruction bắt buộc LLM chỉ trả lời từ Context và thông báo nếu không đủ thông tin.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================== 42 passed in 0.19s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | I want to return a damaged product. | How can a customer send back faulty goods? | cao | -0.0312 | Không |
| 2 | The buyer has fourteen days to cancel. | Customers may withdraw within two weeks. | cao | -0.0038 | Không |
| 3 | A seller must disclose total checkout cost. | Tomorrow will have heavy rain. | thấp | 0.0113 | Có |
| 4 | Extra payments require explicit consent. | The buyer must approve added fees. | cao | -0.1032 | Không |
| 5 | A fixed chunk may cut a sentence. | This soup contains vegetables. | thấp | 0.1102 | Không |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp explicit consent đồng nghĩa nhưng nhận điểm âm, còn cặp chunk/soup không liên quan lại dương. MockEmbedder chỉ deterministic theo chuỗi, vì vậy không thể dùng các điểm này để kết luận chất lượng semantic.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

Lệnh: `python bench.py`. Strategy: `FixedSizeChunker(chunk_size=450, overlap=50)`, 16 chunks, mock embedding.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | How long is the minimum legal guarantee for faulty goods? | Đoạn bắt đầu giữa từ về burden of proof — `eu-guarantees-returns::chunk_1` | 0.1790 | Không | Thiếu câu chứa mốc bảo hành |
| 2 | When can a buyer receive a refund instead of repair or replacement? | Cooling-off exception — `eu-shopping-rights::chunk_1` | 0.2571 | Không | Không có điều kiện repair/refund |
| 3 | What must an online seller do before charging an extra payment at checkout? | Withdrawal — `eu-seller-guarantees::chunk_0` | 0.1061 | Không | Không có explicit consent |
| 4 | Which product problems allow a customer to claim redress from a seller? | Payment setup — `eu-online-shop-rules::chunk_0` | 0.1624 | Không | Không có danh sách redress |
| 5 | Can an online customer return clearly personalised goods during the cooling-off period? | Currency conversion — `eu-pricing-payments::chunk_2` | 0.3079 | Không | Không có personalised goods |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 0 / 5

**Failure case:** Query 1 trả đúng tài liệu ở top-1 nhưng chunk bắt đầu giữa từ “delivery” và không chứa marker `minimum legal guarantee lasts two years`. Fixed-size overlap không bảo đảm câu bằng chứng còn nguyên; đề xuất tăng overlap hoặc chuyển sang sentence/heading boundary, đồng thời giữ nguyên query/corpus để so sánh công bằng.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> SentenceChunker và HeadingChunker cùng đạt 4/10 vì giữ đơn vị ngữ nghĩa trọn vẹn hơn. Fixed-size là baseline hữu ích để thấy overlap 50 vẫn không cứu được evidence khi biên cắt sai vị trí.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 4 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 0 / 10 |
| **Tổng phần cá nhân** | **48 / 60** |
