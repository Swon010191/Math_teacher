# Yêu cầu dự án (REQUIREMENTS)

Tài liệu này tóm tắt các yêu cầu đã chốt cho **AI Teaching Assistant**.
Tài liệu gốc chi tiết: [AI_Teaching_Assistant_Tong_Hop.txt](AI_Teaching_Assistant_Tong_Hop.txt).

## 1. Yêu cầu chức năng - Stage 1 (MVP)

### F1. AI Whiteboard
- F1.1 Vẽ nét tự do bằng chuột/stylus (bút).
- F1.2 Chọn vùng nét vẽ bằng công cụ chọn (marquee).
- F1.3 Thêm text vào bảng.
- F1.4 Chọn, di chuyển, resize, xóa đối tượng.
- F1.5 Zoom và pan bảng.
- F1.6 Thanh công cụ tiếng Việt: Chọn / Bút / Text / Công thức / Xóa / AI / Lưu.
- F1.7 Lưu toàn bộ trạng thái bảng local (IndexedDB) và mở lại.
- F1.8 Export/Import JSON toàn bộ bảng.

### F2. Nhập & nhận dạng công thức
- F2.1 Viết tay là luồng chính: vẽ -> chọn vùng -> gửi Recognition -> hiện kết quả.
- F2.2 Màn hình xác nhận: hiển thị kết quả nhận dạng (LaTeX/biểu thức), giáo viên
  xác nhận hoặc sửa nhanh.
- F2.3 Gõ phím là phương án dự phòng (ô nhập công thức, hỗ trợ LaTeX).
- F2.4 Recognition qua interface `RecognitionProvider` thay thế được:
  Mock (Stage 1) -> Ollama Vision -> Pix2Text -> Production.
- F2.5 Khi Recognition lỗi/không có, gõ phím vẫn hoạt động.

### F3. Math Engine (backend)
- F3.1 Parse biểu thức toán (SymPy).
- F3.2 Hàm bậc hai `y = ax^2 + bx + c`: tính đỉnh, trục đối xứng, nghiệm,
  giao điểm với trục tung/hoành.
- F3.3 Sinh dữ liệu đồ thị.
- F3.4 Tất cả kết quả trả về dạng JSON có schema (Pydantic).
- F3.5 Khi tham số a, b, c thay đổi -> tính lại ngay.

### F4. Interactive Teaching Canvas (Activity hàm bậc hai)
- F4.1 Đồ thị parabol tương tác (JSXGraph).
- F4.2 Slider cho hệ số a, b, c; kéo slider -> đồ thị cập nhật ngay.
- F4.3 Nút hiện/ẩn: đỉnh, nghiệm, trục đối xứng.
- F4.4 Chuỗi bước giảng dạy (teaching steps) - điều khiển nội dung hiện theo bước.
- F4.5 Activity là React component trên lớp DOM, kéo/resize được trên bảng.
- F4.6 Activity Model JSON có `schemaVersion`, export/import được.

### F5. Activity Model
- F5.1 JSON schema có phiên bản (`schemaVersion`).
- F5.2 Chứa: nguồn biểu thức, kết quả Math Engine, widget, teaching steps.
- F5.3 File activity mẫu trong `examples/activities/`.

## 2. Yêu cầu phi chức năng

| Mã | Yêu cầu |
|---|---|
| NFR1 | Mọi dependency là mã nguồn mở, ghi trong THIRD_PARTY_NOTICES.md |
| NFR2 | Build & cài đặt từ mã nguồn, có hướng dẫn |
| NFR3 | Commit có nghĩa lên GitHub; README, CHANGELOG, Issues đầy đủ |
| NFR4 | Local-first: không bắt buộc tài khoản/cloud/API key |
| NFR5 | Khi AI tắt/lỗi, Math Core + Whiteboard vẫn hoạt động |
| NFR6 | Không gửi dữ liệu lớp học ra cloud khi chưa đồng ý |
| NFR7 | UI tiếng Việt |
| NFR8 | Math Engine là nguồn sự thật toán học, LLM không tính toán |
| NFR9 | Mọi đầu ra AI là JSON có schema, validate, giáo viên duyệt trước khi lên bảng |

## 3. Giai đoạn sau (ngoài Stage 1)

- Teacher Copilot: giải thích, sinh câu hỏi, ví dụ, teaching sequence (local AI - Ollama).
- Recognition thật: Ollama + LLaVA/Qwen-VL; Pix2Text cho Math OCR.
- Các loại hàm: bậc nhất, phân thức, sin/cos, logarit, mũ; đạo hàm; hình học.
- Open Activity Platform: plugin SDK, community library, fork/share.
- E2E test (Playwright) hoàn chỉnh.

## 4. Tiêu chí chấp nhận demo (do khách hàng đánh giá)

1. Viết/nhập được hàm bậc hai. 2. Nhận dạng + xác nhận biểu thức. 3. Math Engine
tính đúng. 4. Activity hiện trên bảng. 5. Slider đổi hệ số. 6. Kiểm soát hiện đáp án.
8. Tắt AI, toán + bảng vẫn chạy. 9. Lưu/mở lại bảng. 10. Không cần tài khoản/cloud trả phí.