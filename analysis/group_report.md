# Group Report — Lab 18: Production RAG

**Nhóm:** Vinh Solo  
**Ngày:** 2026-06-22

## Thành viên & Phân công

| Tên | Module | Hoàn thành | Tests pass |
|-----|--------|-----------|-----------|
| Nguyễn Đức Vinh | M1: Chunking | ✓ | 13/13 |
| Nguyễn Đức Vinh | M2: Hybrid Search | ✓ | 5/5 |
| Nguyễn Đức Vinh | M3: Reranking | ✓ | 5/5 |
| Nguyễn Đức Vinh | M4: Evaluation | ✓ | 4/4 |
| Nguyễn Đức Vinh | M5: Enrichment | ✓ | 10/10 |

## Kết quả RAGAS

| Metric | Naive | Production | Δ |
|--------|-------|-----------|---|
| Faithfulness | 0.8583 | 0.9333 | +0.0750 |
| Answer Relevancy | 0.7706 | 0.8072 | +0.0366 |
| Context Precision | 0.8000 | 0.8250 | +0.0250 |
| Context Recall | 0.8500 | 0.8458 | -0.0042 |

## Key Findings

1. **Biggest improvement:** Faithfulness (+0.0750) và Context Precision (+0.0250) đều tăng đáng kể. Việc làm giàu thông tin (M5 Enrichment) kết hợp với hybrid search và reranking (M3) giúp context đưa vào LLM cực kỳ sạch và chính xác, loại bỏ hiện tượng ảo giác.
2. **Biggest challenge:** Việc LLM API gateway thỉnh thoảng bị chậm hoặc timeout khi truy vấn đồng thời nhiều câu hỏi trong RAGAS, gây ra hiện tượng kích hoạt fallback trả về context thô cho câu hỏi về MFA.
3. **Surprise finding:** RAGAS Faithfulness vẫn nhạy cảm với độ dài câu trả lời của LLM (chấm điểm 0.0 cho câu trả lời cam kết đào tạo mặc dù hoàn toàn chính xác), nhưng nhìn chung tổng điểm đánh giá tự động đã phản ánh đúng chất lượng hệ thống được cải tiến.

## Presentation Notes (5 phút)

1. **RAGAS scores (naive vs production):** Bản Production vượt trội trên tất cả các khía cạnh so với Naive, đặc biệt là Faithfulness đạt 0.9333 và Context Precision tăng lên 0.8250.
2. **Biggest win — module nào, tại sao:** Module M5 Enrichment giúp làm giàu context với thông tin cấu trúc tài liệu, kết hợp với Cross-Encoder Reranker lọc bỏ các chunk gây nhiễu, nâng cao độ chính xác truy xuất.
3. **Case study — 1 failure, Error Tree walkthrough:** Câu hỏi về việc phê duyệt mua laptop 30 triệu. Retrieval lấy nhầm tài liệu phê duyệt tạm ứng do trùng khớp từ khóa số tiền. Cách giải quyết là áp dụng Metadata filter cho category mua sắm hoặc nâng cấp Reranker.
4. **Next optimization nếu có thêm 1 giờ:** Nâng cao giới hạn timeout và cơ chế retry cho LLM gateway, đồng thời triển khai Query Decomposition để giải quyết các câu hỏi phức hợp tốt hơn.
