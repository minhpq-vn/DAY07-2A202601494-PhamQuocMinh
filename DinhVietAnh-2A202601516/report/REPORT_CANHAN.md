# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Đinh Việt Anh
**MSSV:** 2A202601516
**Nhóm:** HUST
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

Hai đoạn văn bản có độ tương tự cosine cao nghĩa là vector embedding của chúng trỏ về cùng một hướng trong không gian nhiều chiều, tức là chúng mang ý nghĩa ngữ nghĩa gần nhau. Giá trị gần 1.0 cho thấy hai câu gần như đồng nghĩa hoặc nói về cùng chủ đề.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Cửa hàng chấp nhận đổi trả trong vòng 30 ngày."
- Câu B: "Khách hàng có thể hoàn hàng trong 30 ngày kể từ ngày mua."
- Tại sao tương đồng: Cả hai đều nói về chính sách đổi/hoàn hàng với thời hạn 30 ngày — cùng chủ đề, cùng thông tin cốt lõi dù dùng từ khác nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Chính sách giao hàng nhanh trong 2 ngày làm việc."
- Câu B: "Con mèo đang ngồi trên mái nhà."
- Tại sao khác: Hai câu thuộc hoàn toàn hai lĩnh vực khác nhau (thương mại điện tử vs. mô tả vật thể), không có điểm chung về ngữ nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

Cosine similarity đo góc giữa hai vector chứ không phải độ dài, nên nó không bị ảnh hưởng bởi độ dài văn bản — một câu ngắn và một đoạn văn dài nói cùng chủ đề vẫn có thể có cosine cao. Khoảng cách Euclid lại bị chi phối bởi độ lớn (magnitude) của vector, khiến văn bản dài luôn bị coi là "xa" hơn dù nội dung tương đồng.

---

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

Áp dụng công thức:

```
số_chunk = ceil((doc_length - overlap) / (chunk_size - overlap))
         = ceil((10000 - 50) / (500 - 50))
         = ceil(9950 / 450)
         = ceil(22.11)
         = 23 chunks
```

**Nếu overlap tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**

```
= ceil((10000 - 100) / (500 - 100))
= ceil(9900 / 400)
= ceil(24.75)
= 25 chunks
```

Overlap tăng → step giảm → số chunk tăng lên. Overlap nhiều hơn giúp bảo toàn ngữ cảnh tại ranh giới giữa các chunk — câu hoặc ý tưởng bị cắt ngang ở cuối chunk này sẽ xuất hiện đầy đủ ở chunk tiếp theo, giúp retrieval không bị mất thông tin biên.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

Dùng regex `(?<=[.!?])(?:\s+|\n)` để tách câu — lookbehind đảm bảo chỉ tách sau dấu `.`, `!`, `?`, giữ nguyên dấu câu ở cuối mỗi phần. Sau đó gom từng nhóm `max_sentences_per_chunk` câu lại thành một chunk bằng `" ".join(group)`. Edge case xử lý: text rỗng trả về `[]`, các phần rỗng sau split được lọc bỏ qua `strip()`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

Thuật toán thử lần lượt các separator từ thô nhất (`\n\n`) đến chi tiết nhất (`""`). Tại mỗi bước, split text bằng separator hiện tại rồi gom các phần lại thành nhóm vừa `chunk_size`; nếu một phần đơn lẻ vẫn vượt kích thước thì gọi đệ quy với separator tiếp theo. Base case là khi text đã đủ nhỏ (`<= chunk_size`) — trả về ngay lập tức, hoặc khi hết separator — force-split theo ký tự.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

Mỗi `Document` được embed content thành vector rồi lưu vào `self._store` dưới dạng dict gồm `id`, `content`, `embedding`, `metadata`. Khi search, embed query rồi tính dot product với từng embedding đã lưu, sort giảm dần theo score, cắt lấy `top_k`. Dùng dot product thay vì cosine đầy đủ vì mock embeddings đã được normalize về độ dài 1 nên kết quả tương đương.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

`search_with_filter` lọc trước — chỉ giữ lại các record có metadata khớp toàn bộ các key-value trong `metadata_filter`, rồi mới chạy similarity search trên tập đã lọc. `delete_document` xóa bằng cách rebuild `self._store` loại bỏ tất cả record có `metadata["doc_id"] == doc_id`, trả `True` nếu số lượng thực sự giảm.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

Retrieve `top_k` chunks từ store, format chúng thành danh sách đánh số `[1] content\n[2] content...` làm phần context. Prompt có cấu trúc rõ ràng: mở đầu bằng instruction ("Use the following context..."), tiếp theo là Context block, cuối là Question và "Answer:" để LLM điền vào. Cách inject context theo số thứ tự giúp LLM dễ tham chiếu lại nguồn.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết Quả Kiểm Thử (Test Results)

```
========================================== test session starts ==========================================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED             [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                      [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED               [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                     [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED     [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED           [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED            [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED          [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                            [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED            [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                       [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                   [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                             [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED    [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED        [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED  [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED        [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                            [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED              [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                      [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED           [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED             [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED              [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                       [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                      [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                 [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED             [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED        [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED            [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                  [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED            [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED       [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED      [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED     [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

========================================== 42 passed in 0.19s ===========================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> Lưu ý: các điểm dưới đây được tính bằng `MockEmbedder` (deterministic nhưng gần như ngẫu nhiên theo chuỗi ký tự). Kết quả không phản ánh ngữ nghĩa thực — để so sánh ngữ nghĩa tiếng Việt cần dùng `LocalEmbedder`.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|-----|-------|-------|---------|--------------|-------|
| 1 | Chính sách đổi trả hàng trong 30 ngày. | Khách hàng được hoàn tiền nếu trả hàng trong 30 ngày. | cao | 0.1329 | ✗ (mock ngẫu nhiên) |
| 2 | Phương thức thanh toán bao gồm thẻ tín dụng và ví điện tử. | Bạn có thể thanh toán bằng thẻ Visa hoặc MasterCard. | cao | 0.1292 | ✗ (mock ngẫu nhiên) |
| 3 | Chính sách giao hàng nhanh trong 2 ngày. | Con mèo đang ngồi trên mái nhà. | thấp | -0.0622 | ✓ |
| 4 | Người bán cần đăng ký tài khoản để đăng sản phẩm. | Điều kiện trở thành người bán trên sàn thương mại điện tử. | cao | 0.2906 | ✓ (tương đối cao nhất) |
| 5 | Quyền riêng tư của khách hàng được bảo vệ theo luật. | Giá vàng hôm nay tăng mạnh. | thấp | 0.0254 | ✓ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

Bất ngờ nhất là cặp 1 và 2 — hai câu rõ ràng đồng nghĩa với nhau nhưng điểm cosine chỉ khoảng 0.13, không cao hơn nhiều so với các cặp không liên quan. Điều này cho thấy `MockEmbedder` hash theo ký tự chứ không hiểu ngữ nghĩa — vector của nó hoàn toàn ngẫu nhiên theo chuỗi ký tự đầu vào. Để có kết quả phản ánh ý nghĩa thật, cần dùng mô hình embedding thực như `LocalEmbedder` (`paraphrase-multilingual-MiniLM-L12-v2`).

---

## 5. Kết quả truy xuất của tôi — Cá nhân (10 điểm)

> Lệnh: `python bench.py`. Strategy: `SentenceChunker(max_sentences_per_chunk=3)`, 18 chunks, mock embedding.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? | Câu trả lời của Agent (tóm tắt) |
|---|-----------------|---------------------------------------|------------|---------------------|----------------------------------|
| 1 | How long is the minimum legal guarantee for faulty goods? | Legal guarantee — `eu-guarantees-returns::chunk_0` | 0.1847 | Có, top-1 | Context chứa mốc hai năm |
| 2 | When can a buyer receive a refund instead of repair or replacement? | Seller status — `eu-shopping-rights::chunk_0` | 0.0679 | Không | Context thiếu điều kiện hoàn tiền |
| 3 | What must an online seller do before charging an extra payment at checkout? | Redress conditions — `eu-seller-guarantees::chunk_1` | 0.1126 | Có, top-2 | Context top-2 chứa explicit consent |
| 4 | Which product problems allow a customer to claim redress from a seller? | PSP registration — `eu-online-shop-rules::chunk_1` | 0.1141 | Không | Không có marker danh sách redress |
| 5 | Can an online customer return clearly personalised goods during the cooling-off period? | Pre-ticked box — `eu-pricing-payments::chunk_1` | 0.1738 | Có, top-3 | Context top-3 chứa personalised goods |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 3 / 5

**Failure case:** Query 4 có top-1 về payment provider dù gold là danh sách lỗi sản phẩm. Chunk đúng câu nhưng ranking mock sai chủ đề; đổi sang local embedding là sửa chính, không đổi query sau khi đã xem kết quả.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

HeadingChunker giữ tiêu đề trên từng mảnh dài, còn SentenceChunker của tôi đưa số liệu bảo hành lên top-1. Hai kết quả cho thấy ranh giới câu và provenance section bổ sung cho nhau.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 4 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 4 / 10 |
| **Tổng phần cá nhân** | **53 / 60** |
