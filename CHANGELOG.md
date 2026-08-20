# Changelog

Tất cả thay đổi đáng chú ý của dự án sẽ được ghi lại trong file này.

Định dạng dựa trên [Keep a Changelog](https://keepachangelog.com/vi/1.1.0/),
dự án tuân thủ [Semantic Versioning](https://semver.org/lang/vi/).

## [Chưa phát hành]

### Đã thêm (Stage 1 - MVP)
- Công cụ **Di chuyển**: nhấn và kéo để dời bảng (bổ sung cho chuột giữa).
- Đèn trạng thái **AI sẵn sàng / AI chưa kết nối** trên thanh công cụ: kiểm tra
  `/health` tự động mỗi 10 giây, giúp nhận biết ngay khi backend chưa chạy
  (nguyên nhân lỗi "failed to fetch").
- API client gọi qua cùng origin (proxy Vite `/api`), hết phụ thuộc CORS; báo
  lỗi rõ ràng khi không kết nối được máy chủ AI.
- Backend Math Engine (FastAPI + SymPy): phân tích biểu thức, tính đỉnh/nghiệm/
  trục đối xứng/giao điểm trục, sinh điểm mẫu đồ thị; 27 test.
- Backend Recognition Service với MockRecognitionProvider (Stage 1), kiến trúc
  provider thay thế được.
- Activity Model (schemaVersion 1.0) + API tạo activity hàm bậc hai.
- Frontend AI Whiteboard (React + Vite + TS + react-konva + Zustand): bút vẽ,
  chọn/di chuyển/xóa đối tượng, zoom/pan, text, lưu IndexedDB, JSON export/import.
- Luồng nhận dạng: khoanh vùng nét vẽ -> gửi Recognition -> modal xác nhận/sửa
  -> tạo activity; nhập công thức bằng bàn phím là dự phòng.
- Interactive Teaching Canvas (JSXGraph): đồ thị parabol, slider a/b/c, nút
  hiện/ẩn đỉnh-nghiệm-trục, điều hướng bước giảng dạy, kéo/resize trên bảng.
- Kiểm thử frontend (Vitest + React Testing Library): 14 test.
- Kiểm thử E2E (Playwright): 3 test cho luồng vẽ -> nhận dạng -> xác nhận ->
  trực quan hóa, nhập công thức bằng bàn phím, lưu/mở bảng.
- Tài liệu mã nguồn mở: README, CHANGELOG, CONTRIBUTING, THIRD_PARTY_NOTICES,
  hướng dẫn cài đặt, issue templates (bug tracker GitHub Issues).

### Đã sửa (Stage 1)
- Công cụ Chọn và Xóa chuyển sang **khoanh vùng (marquee)**: kéo khung bao quanh
  để chọn/xóa toàn bộ đối tượng trong vùng, không cần bấm trúng từng nét vẽ.
- Chọn nhiều đối tượng cùng lúc và kéo di chuyển cả nhóm; activity cũng được
  khoanh vùng chọn và hiển thị viền xanh khi được chọn.
- Thêm 2 test E2E cho khoanh vùng Chọn và Xóa (tổng 5 test E2E).
- Thêm 1 test E2E cho công cụ Di chuyển (tổng 6 test E2E).

### Sắp tới
- Teacher Copilot (Generative AI) - giải thích, sinh câu hỏi, đề xuất teaching sequence.
- Open Teaching Activity Platform - plugin, chia sẻ cộng đồng.
- Các loại hàm khác: bậc nhất, phân thức, sin/cos, logarit, mũ.
- Tích hợp Recognition thực (Ollama + LLaVA/Qwen-VL, Pix2Text) thay Mock Provider.