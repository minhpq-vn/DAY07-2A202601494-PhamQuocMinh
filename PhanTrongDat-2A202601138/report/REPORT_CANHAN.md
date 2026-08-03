# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phan Trọng Đạt
**Nhóm:** HUST
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai đoạn văn bản có độ tương tự cosine cao nghĩa là các vector biểu diễn không gian (embeddings) của chúng hướng về cùng một góc/hướng trong không gian đa chiều, thể hiện rằng hai đoạn văn bản có **ngữ nghĩa tương đồng hoặc cùng bàn về một chủ đề**, dù từ ngữ thực tế có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- **Câu A:** "Mô hình AI này có khả năng xử lý ngôn ngữ tự nhiên rất mượt mà."
- **Câu B:** "Trí tuệ nhân tạo này phân tích và hiểu văn bản tiếng Việt cực kỳ tốt."
- **Tại sao tương đồng:** Dù dùng các từ khác nhau (xử lý ngôn ngữ tự nhiên vs phân tích và hiểu văn bản), cả hai câu đều mang cùng một hàm ý ngữ nghĩa về năng lực hiểu văn bản của mô hình AI.

**Ví dụ có độ tương tự THẤP:**
- **Câu A:** "Hôm nay trời nắng đẹp thích hợp đi dã ngoại cùng bạn bè."
- **Câu B:** "Thuật toán sắp xếp nhanh QuickSort có độ phức tạp thời gian trung bình là O(n log n)."
- **Tại sao khác:** Hai câu thuộc hai chủ đề hoàn toàn độc lập (thời tiết/sinh hoạt vs thuật toán máy tính), không có mối quan hệ ngữ nghĩa nào.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid bị ảnh hưởng mạnh bởi độ dài của văn bản (độ lớn/chuẩn của vector), khiến một đoạn văn ngắn và một đoạn văn dài dù cùng ý nghĩa vẫn có khoảng cách Euclid xa. Trái lại, Cosine Similarity chỉ đo góc giữa 2 vector (hướng), bỏ qua độ dài vector, giúp phản ánh chính xác sự tương đồng ngữ nghĩa bất kể độ dài văn bản ngắn hay dài.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> **Trình bày phép tính:**
> $$\text{số chunk} = \text{ceil}\left(\frac{\text{độ dài tài liệu} - \text{overlap}}{\text{chunk\_size} - \text{overlap}}\right) = \text{ceil}\left(\frac{10000 - 50}{500 - 50}\right) = \text{ceil}\left(\frac{9950}{450}\right) = \text{ceil}(22.111) = 23$$
> **Đáp án:** **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> - **Thay đổi số chunk:** Số lượng chunk sẽ **TĂNG từ 23 lên 25 chunks** ($\text{ceil}\left(\frac{10000 - 100}{500 - 100}\right) = \text{ceil}(24.75) = 25$).
> - **Lý do tăng overlap:** Giúp giữ lại ngữ cảnh ở các ranh giới giữa các chunk (ranh giới câu/ý nghĩa không bị cắt đứt đột ngột), giúp quá trình tìm kiếm truy xuất (retrieval) không bị hổng thông tin nằm ở đoạn nối.
> - **Sự đánh đổi:** Tăng số lượng chunk sẽ làm **tăng dung lượng lưu trữ** trong Vector Store, **tăng thời gian nhúng (embedding computation)** và **tốn nhiều token hơn** khi đưa thông tin vào LLM context.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng biểu thức chính quy `re.split(r'(?<=[.!?])\s+', text)` để tìm ranh giới kết thúc câu (sau các dấu `.`, `!`, `?` có khoảng trắng hoặc xuống dòng) mà vẫn giữ nguyên dấu câu ở cuối từng câu. Các edge case như chuỗi rỗng, khoảng trắng thừa ở hai đầu câu được xử lý bằng `strip()` và lọc bỏ câu rỗng; sau đó nhóm các câu lại theo kích thước tối đa `max_sentences_per_chunk` bằng `join()`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán chia nhỏ đệ quy theo thứ tự ưu tiên các separator từ lớn đến nhỏ (đoạn `\n\n` -> dòng `\n` -> câu `. ` -> từ ` ` -> ký tự `""`). Base case 1 dừng khi văn bản có độ dài $\le$ `chunk_size`. Base case 2 là khi hết separator hoặc separator rỗng thì cắt cố định theo `chunk_size`. Với mỗi separator xuất hiện, thuật toán gộp các mảnh liền kề cho đến khi chạm tới `chunk_size`; mảnh nào quá dài sẽ tiếp tục được chia đệ quy với danh sách separator ưu tiên thấp hơn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu trữ văn bản dưới dạng danh sách các record chuẩn hóa chứa `id`, `content`, bản sao `metadata` và vector `embedding` được tính từ `_embedding_fn`. Hàm `search` sử dụng helper `_search_records` để tính tích vô hướng (dot product) giữa query embedding và tất cả các embedding đã lưu, sau đó sắp xếp giảm dần theo điểm số `score` để cắt ra `top_k` kết quả tốt nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` thực hiện quy trình **Lọc trước (pre-filtering), Xếp hạng sau (post-ranking)**: lọc các record trong store thỏa mãn tất cả cặp key-value trong `metadata_filter` trước khi gọi `_search_records` để tìm kiếm trên tập ứng viên. `delete_document` duyệt qua các record và loại bỏ những chunk có `metadata['doc_id']` hoặc `id` trùng khớp với `doc_id` truyền vào.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Đợt đầu truy xuất `top_k` chunk liên quan từ `EmbeddingStore` dựa trên câu hỏi. Đánh số thứ tự từng chunk dưới dạng `[1] (doc_id) content` để đưa vào prompt dưới dạng ngữ cảnh (Context), kèm theo hướng dẫn LLM chỉ trả lời dựa vào ngữ cảnh này (nếu thiếu context phải báo rõ). Cuối cùng truyền prompt vào `llm_fn` để sinh câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================= 42 passed in 0.90s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | This AI model understands natural language. | The artificial intelligence system can process text. | cao | -0.0133 | Không |
| 2 | Today is sunny enough for a picnic. | Quicksort has average complexity O(n log n). | thấp | -0.2704 | Có |
| 3 | Faulty goods have a two-year guarantee. | Defective products are protected for two years. | cao | 0.1385 | Không rõ với mock |
| 4 | Extra payments require customer consent. | The buyer must approve additional checkout fees. | cao | -0.0417 | Không |
| 5 | A private seller is not a professional trader. | Credit cards may require authentication. | thấp | -0.0966 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp AI đồng nghĩa lại có điểm âm, chứng minh MockEmbedder deterministic nhưng không hiểu nghĩa. Vì vậy benchmark mock chỉ dùng để kiểm flow, chunk coherence và provenance.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

Lệnh: `python bench.py`. Strategy: `RecursiveChunker(chunk_size=350)`, 26 chunks, mock embedding.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | How long is the minimum legal guarantee for faulty goods? | Card surcharge — `eu-pricing-payments::chunk_2` | 0.2448 | Không | Context thiếu mốc hai năm |
| 2 | When can a buyer receive a refund instead of repair or replacement? | Commercial guarantees — `eu-guarantees-returns::chunk_2` | 0.1337 | Không | Không có điều kiện refund |
| 3 | What must an online seller do before charging an extra payment at checkout? | Checkout duties — `eu-online-shop-rules::chunk_2` | 0.1210 | Có, top-1 | Context chứa explicit consent và total cost |
| 4 | Which product problems allow a customer to claim redress from a seller? | Heading `Available remedies` — `eu-seller-guarantees::chunk_4` | 0.2583 | Không | Đúng doc nhưng sai section |
| 5 | Can an online customer return clearly personalised goods during the cooling-off period? | Legal guarantee — `eu-guarantees-returns::chunk_0` | 0.2638 | Có, top-2 | Context top-2 chứa personalised goods |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 2 / 5

**Failure case:** Query 4 trả đúng `doc_id` ở top-1 nhưng chunk chỉ có heading “Available remedies”; marker `does not match its description` không có trong top-3. Chunk size 350 tạo 26 mảnh và làm loãng cơ hội section gold lọt top-k; đề xuất heading-aware fallback hoặc tăng chunk size.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> HeadingChunker gắn lại tiêu đề khi section dài, tránh mảnh mất provenance như failure của tôi. SentenceChunker cũng cho thấy câu hoàn chỉnh có thể đưa số liệu lên top-1.

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
