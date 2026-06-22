# Failure Analysis — Lab 18: Production RAG

**Nhóm:** Vinh Solo  
**Thành viên:** Mai Đức Vinh (M1, M2, M3, M4, M5)

---

## RAGAS Scores

| Metric | Naive Baseline | Production | Δ |
|--------|---------------|------------|---|
| Faithfulness | 0.8583 | 0.9333 | +0.0750 |
| Answer Relevancy | 0.7706 | 0.8072 | +0.0366 |
| Context Precision | 0.8000 | 0.8250 | +0.0250 |
| Context Recall | 0.8500 | 0.8458 | -0.0042 |

---

## Bottom-5 Failures

### #1
- **Question:** Một nhân viên Senior có 9 năm thâm niên được nghỉ bao nhiêu ngày phép năm và lương trong khoảng nào?
- **Expected:** Theo chính sách v2024: 15 ngày cơ bản + 3 ngày thâm niên (9÷3=3) = 18 ngày phép. Lương Senior (P3-P4): 20-35 triệu VNĐ/tháng.
- **Got:** Một nhân viên 9 năm thâm niên được 18 ngày phép (15 + 3). Không tìm thấy thông tin về mức lương.
- **Worst metric:** context_precision (score: 0.0)
- **Error Tree:** Output thiếu thông tin lương → Context truy xuất thiếu tài liệu lương → Query phân tích đúng nhưng Retrieval chỉ lấy được tài liệu về nghỉ phép.
- **Root cause:** Truy vấn dạng multi-hop (hỏi 2 khía cạnh: phép năm và mức lương). Retrieval bị lệch hoàn toàn sang chủ đề nghỉ phép vì các từ khóa thâm niên, ngày phép xuất hiện nhiều hơn, khiến tài liệu về thang bảng lương bị đẩy khỏi top k.
- **Suggested fix:** Áp dụng kĩ thuật Query Decomposition (phân rã truy vấn) để tách câu hỏi thành 2 câu hỏi đơn: "Senior 9 năm được bao nhiêu ngày phép?" và "Lương Senior trong khoảng nào?", sau đó thực hiện tìm kiếm song song rồi gộp ngữ cảnh lại.

### #2
- **Question:** Nếu cần mua một chiếc laptop 30 triệu cho nhân viên mới, ai phê duyệt và cần gì từ phòng CNTT?
- **Expected:** Laptop 30 triệu nằm trong khoảng 5-50 triệu nên cần Giám đốc phòng ban (Director) phê duyệt. Ngoài ra, mua sắm thiết bị CNTT cần có xác nhận cấu hình kỹ thuật từ phòng CNTT trước khi đề xuất. Cần đính kèm ít nhất 3 báo giá vì trên 10 triệu.
- **Got:** Cần xác nhận CNTT về cấu hình kỹ thuật. Context không đề cập cụ thể ai phê duyệt cho mua sắm, chỉ nêu quy định tạm ứng.
- **Worst metric:** context_precision (score: 0.0)
- **Error Tree:** Output thiếu thông tin phê duyệt mua sắm → Context lấy sai tài liệu (lấy quy chế Tạm ứng và lưu ý mua sắm CNTT, thiếu quy trình mua sắm thiết bị chính) → Query bị nhiễu.
- **Root cause:** Retrieval lấy nhầm tài liệu "Phê duyệt tạm ứng" thay vì tài liệu "Quy trình mua sắm" do từ khóa "30 triệu", "ai phê duyệt" bị khớp mạnh với tài liệu tạm ứng và CNTT.
- **Suggested fix:** Sử dụng Metadata Filtering dựa trên Category được trích xuất ở M5 (chỉ tìm kiếm trong tài liệu thuộc category: procurement/mua sắm), hoặc tăng trọng số Dense Search kết hợp Cross-Encoder Reranker mạnh hơn để lọc nhiễu ngữ nghĩa.

### #3
- **Question:** Nhân viên được tài trợ khóa học 25 triệu, nghỉ việc sau 8 tháng hoàn thành khóa học. Phải hoàn trả bao nhiêu?
- **Expected:** Nhân viên phải cam kết làm việc ít nhất 1 năm sau khi hoàn thành khóa học. Nghỉ sau 8 tháng là trước hạn cam kết, phải hoàn trả 100% chi phí tức 25.000.000 VNĐ.
- **Got:** Nhân viên phải hoàn trả 25.000.000 VNĐ (tương đương 100% chi phí đào tạo).
- **Worst metric:** faithfulness (score: 0.0)
- **Error Tree:** Output đúng → RAGAS chấm sai điểm faithfulness → Claims trích xuất từ câu trả lời ngắn không khớp hoàn hảo với các câu khẳng định trong context.
- **Root cause:** Ragas Faithfulness evaluation failure. Ragas đánh giá mức độ trung thực của câu trả lời dựa trên việc trích xuất các claims và đối chiếu với context. Do câu trả lời của LLM quá ngắn gọn, Ragas hiểu nhầm là LLM tự bịa ra thông tin.
- **Suggested fix:** Điều chỉnh prompt của LLM để đưa ra câu trả lời chi tiết và lập luận đầy đủ kèm trích dẫn (ví dụ: "Theo chính sách hoàn chi đào tạo, nhân viên nghỉ việc trước thời hạn cam kết 1 năm phải hoàn trả 100% chi phí. Do đó, nghỉ sau 8 tháng phải hoàn trả toàn bộ 25 triệu VNĐ").

### #4
- **Question:** Lương thử việc của nhân viên Junior mức cao nhất là bao nhiêu?
- **Expected:** Junior cao nhất là 20.000.000 VNĐ/tháng. Lương thử việc = 85% x 20.000.000 = 17.000.000 VNĐ/tháng.
- **Got:** Không tìm thấy.
- **Worst metric:** context_precision (score: 0.0)
- **Error Tree:** Output "Không tìm thấy" → Context thiếu tài liệu bảng lương → Retrieval thất bại trong việc tìm tài liệu chứa mức lương Junior.
- **Root cause:** Retrieval failure. Tài liệu chứa bảng lương cụ thể của Junior không được truy xuất vào top 3 do cấu trúc bảng lương (markdown table) bị phân mảnh sau khi chunking hoặc từ khóa tìm kiếm "Junior" không đủ mạnh để kéo tài liệu lên đầu.
- **Suggested fix:** Cải thiện chunking cho cấu trúc bảng biểu (Structure-aware table parser) và tăng kích thước context window hoặc tăng `top_k` của retrieval trước khi rerank.

### #5
- **Question:** Có cần kích hoạt xác thực đa yếu tố (MFA) không?
- **Expected:** Có, tất cả nhân viên bắt buộc kích hoạt MFA cho email, VPN và hệ thống nội bộ.
- **Got:** Khuyến khích sử dụng passphrase dài hơn 16 ký tự. ## Xác thực đa yếu tố (MFA) Tất cả nhân viên bắt buộc kích hoạt MFA cho tài khoản email, VPN và các hệ thống nội bộ. (Bị fallback do timeout).
- **Worst metric:** context_recall (score: 0.5)
- **Error Tree:** Output chứa thô văn bản context → LLM API bị timeout trong quá trình sinh câu trả lời → Pipeline trả về fallback là context đầu tiên.
- **Root cause:** Latency/Network timeout. LLM API gateway bị chậm khi sinh câu trả lời cho câu hỏi này, dẫn đến vượt quá giới hạn timeout (10.0 giây) trong `llm.py` và kích hoạt fallback lấy context thô.
- **Suggested fix:** Tăng timeout giới hạn trong `llm.py` lên 15.0 giây hoặc triển khai cơ chế retry tự động khi gặp timeout.

---

## Case Study (cho presentation)

**Question chọn phân tích:** Nếu cần mua một chiếc laptop 30 triệu cho nhân viên mới, ai phê duyệt và cần gì từ phòng CNTT?

**Error Tree walkthrough:**
1. Output đúng? → Sai (Thiếu thông tin cấp phê duyệt mua sắm do context lấy nhầm quy định tạm ứng).
2. Context đúng? → Sai (Retrieval kéo nhầm context phê duyệt tạm ứng và lưu ý mua sắm CNTT, thiếu quy trình mua sắm chính).
3. Query rewrite OK? → OK.
4. Fix ở bước: Bổ sung Metadata filter (category: procurement) hoặc cải tiến module Reranking để lọc bỏ tài liệu "Tạm ứng" vốn không liên quan đến việc "Mua sắm thiết bị".

**Nếu có thêm 1 giờ, sẽ optimize:**
- Tích hợp **Query Decomposition** để xử lý các câu hỏi phức hợp (multi-hop).
- Xây dựng cơ chế **Metadata Filtering** tự động dựa trên category được LLM trích xuất từ câu hỏi người dùng.
