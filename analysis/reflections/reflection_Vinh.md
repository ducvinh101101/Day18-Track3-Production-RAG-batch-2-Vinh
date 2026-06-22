# Individual Reflection — Lab 18

**Tên:** Nguyễn Đức Vinh  
**Module phụ trách:** Tất cả các modules (M1 → M5)

---

## 1. Đóng góp kỹ thuật

- Module đã implement:
  - **M1 Chunking**: Semantic Chunking (all-MiniLM-L6-v2), Hierarchical Parent-Child Chunking (parent: 2048 chars, child: 256 chars), và Structure-Aware Chunking (markdown header splitting).
  - **M2 Hybrid Search**: Phân tách từ tiếng Việt (underthesea), BM25Search (rank_bm25), DenseSearch (Qdrant), và Reciprocal Rank Fusion (RRF).
  - **M3 Reranking**: Cross-encoder reranker (BAAI/bge-reranker-v2-m3) để sắp xếp lại top 20 tài liệu xuống top 3.
  - **M4 Evaluation**: Tích hợp RAGAS với 4 metrics (faithfulness, answer_relevancy, context_precision, context_recall) sử dụng gateway LLM và phân tích failures.
  - **M5 Enrichment**: Cải tiến tài liệu bằng cách tóm tắt, tạo câu hỏi giả định (HyQA), Contextual Prepend và trích xuất Metadata (hỗ trợ single-call và multi-call).
- Các hàm/class chính đã viết:
  - `chunk_semantic`, `chunk_hierarchical`, `chunk_structure_aware` trong `src/m1_chunking.py`.
  - `segment_vietnamese`, `BM25Search`, `DenseSearch`, `reciprocal_rank_fusion` trong `src/m2_search.py`.
  - `CrossEncoderReranker.rerank`, `FlashrankReranker.rerank` trong `src/m3_rerank.py`.
  - `evaluate_ragas`, `failure_analysis` trong `src/m4_eval.py`.
  - `summarize_chunk`, `generate_hypothesis_questions`, `contextual_prepend`, `extract_metadata`, `_enrich_single_call` trong `src/m5_enrichment.py`.
- Số tests pass: 37/37 tests.

## 2. Kiến thức học được

- Khái niệm mới nhất: RRF (Reciprocal Rank Fusion) kết hợp ưu điểm của cả lexical search (BM25) và semantic search (Dense). Contextual Prepend (prepend document info) giúp LLM không bị mất bối cảnh khi đọc các child chunks nhỏ.
- Điều bất ngờ nhất: RAGAS đánh giá RAG tự động rất tiện lợi, nhưng tốn nhiều thời gian gọi LLM gateway để đánh giá hàng loạt câu hỏi. Ngoài ra, việc dùng Single-call Enrichment giúp giảm tối đa token sử dụng và latency so với gọi 4 API riêng biệt.
- Kết nối với bài giảng (slide nào): Slide về advanced chunking (hierarchical, semantic), hybrid search & RRF fusion, Cross-encoder reranking, và các RAGAS metrics.

## 3. Khó khăn & Cách giải quyết

- Khó khăn lớn nhất: Lỗi không tương thích của package `numpy` trên Python 3.13 (`OverflowError: cannot convert longdouble infinity to integer`).
- Cách giải quyết: Sử dụng môi trường ảo `.venv` chạy Python 3.12.8 thay vì python mặc định của hệ thống.
- Thời gian debug: 15 phút.

## 4. Nếu làm lại

- Sẽ làm khác điều gì: Sử dụng hybrid search kết hợp thêm các filter metadata thông minh được trích xuất từ M5 để tăng độ chính xác trong truy xuất.
- Module nào muốn thử tiếp: Module M5 Enrichment, để thử nghiệm các prompt sinh metadata đa dạng hơn và đánh giá tác động cụ thể lên RAGAS.

## 5. Tự đánh giá

| Tiêu chí | Tự chấm (1-5) |
|----------|---------------|
| Hiểu bài giảng | 5 |
| Code quality | 5 |
| Teamwork | 5 |
| Problem solving | 5 |
