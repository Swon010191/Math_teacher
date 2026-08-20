# Changelog

Tất cả thay đổi đáng chú ý của dự án sẽ được ghi lại trong file này.

Định dạng dựa trên [Keep a Changelog](https://keepachangelog.com/vi/1.1.0/),
dự án tuân thủ [Semantic Versioning](https://semver.org/lang/vi/).

## [Chưa phát hành]

### Đã thêm (Stage 1 - MVP)
- **Kiểm tra khả dụng provider nhận dạng**: popover "AI sẵn sàng" hiển thị
  trạng thái từng provider (✓ khả dụng / ✗ chưa khả dụng kèm hướng dẫn cài đặt
  Ollama/Pix2Text) + nút "Kiểm tra lại"; API mới GET
  `/api/recognize/providers/status` (ping song song, không chạy trong poll định kỳ;
  chọn provider chưa khả dụng sẽ hiện hướng dẫn cài đặt trong toast).
- **Đổi nguồn gợi ý Copilot ngay trên giao diện**: panel "Trợ lý giảng dạy"
  thêm dropdown chọn `rule_based` (gợi ý có sẵn, không cần AI) / `ollama` (AI
  local) - API mới GET/PUT `/api/copilot/provider`, đổi lúc chạy, restart trở về
  `.env`; đổi xong tự tải lại nội dung gợi ý.
- **Teacher Copilot (Stage 3, phần lõi)**: nút "💡 Gợi ý" trên mỗi activity mở
  panel đề xuất nội dung giảng dạy (tóm tắt, kiến thức trọng tâm, câu hỏi gợi
  mở, ví dụ minh họa, chuỗi bước giảng dạy) — **giáo viên duyệt rồi mới lên
  bảng**. API mới `POST /api/copilot/suggest`; mặc định dùng
  `RuleBasedCopilotProvider` (không cần AI), có thể bật `COPILOT_PROVIDER=ollama`
  để dùng LLM local (Ollama) với `OLLAMA_MODEL_COPILOT`; mọi số liệu đều lấy từ
  Math Engine, LLM không được tự tính toán.
- **CI tự động (GitHub Actions)**: mỗi lần push lên main hoặc mở PR sẽ chạy
  backend pytest (41 test), frontend vitest + build (26 test) và E2E Playwright
  (10 test); Playwright có thể nhận `BACKEND_PYTHON` để chạy trên nhiều hệ điều hành.
- **Workflow phát hành**: push tag `v*` tự tạo GitHub Release kèm ghi chú tự sinh.
- **Đổi provider nhận dạng ngay trên giao diện**: bấm vào chip "AI sẵn sàng"
  mở popover xem và chuyển đổi giữa Mock / Ollama Vision / Pix2Text (API mới
  GET/PUT `/api/recognize/provider`; đổi trong lúc chạy, restart trở về .env).
- **Sửa đèn AI luôn xanh**: Vite proxy giờ chuyển tiếp cả `/health` về backend
  (trước đây `/health` bị Vite trả về index.html 200 dù backend chết).
- **Recognition thật (tùy chọn theo cấu hình)**: `OllamaVisionProvider`
  (LLaVA/Qwen-VL qua Ollama) và `Pix2TextProvider` (Math OCR); chọn bằng
  `RECOGNITION_PROVIDER=mock|ollama_vision|pix2text` trong `.env`.
  Mặc định vẫn là Mock - demo không cần cài thêm gì.
- **Activity hàm bậc nhất (linear function)**: API `/api/math/activity` tự chọn
  loại activity theo loại biểu thức (bậc hai/bậc nhất); frontend thêm
  LinearActivity - đồ thị đường thẳng (JSXGraph), slider hệ số a/b, nút hiện
  giao điểm trục x, chuỗi bước giảng dạy, stats cắt trục y.
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
- Hết lỗi treo "Đang phân tích...": nút xác nhận (RecognitionModal) và nút phân
  tích (MathInputBar) luôn thoát khỏi trạng thái busy dù thành công hay thất bại
  (try/finally), nút Hủy luôn bấm được, phím Escape đóng được modal.
- API client có timeout 20 giây (AbortSignal) - không treo vô hạn khi backend chết.
- Công cụ Chọn và Xóa chuyển sang **khoanh vùng (marquee)**: kéo khung bao quanh
  để chọn/xóa toàn bộ đối tượng trong vùng, không cần bấm trúng từng nét vẽ.
- Chọn nhiều đối tượng cùng lúc và kéo di chuyển cả nhóm; activity cũng được
  khoanh vùng chọn và hiển thị viền xanh khi được chọn.
- Thêm 2 test E2E cho khoanh vùng Chọn và Xóa (tổng 5 test E2E).
- Thêm 1 test E2E cho công cụ Di chuyển (tổng 6 test E2E).
- Thêm 2 test E2E cho luồng lỗi: công thức không xác định được vẫn thoát được
  (tổng 8 test E2E) + 4 test đơn vị mới cho RecognitionModal và MathInputBar.
- Thêm activity hàm bậc nhất: 1 test backend, 3 test đơn vị LinearActivity,
  1 test E2E (tổng backend 28, frontend 21, E2E 9).
- Thêm 10 test provider Recognition thật (Ollama Vision + Pix2Text với HTTP
  mock) - tổng backend 37.
- Thêm 5 test Provider API/health + 5 test Toolbar popover - tổng backend 41,
  frontend 26, E2E 10.
- Thêm Teacher Copilot: 8 test backend (API + provider rule_based/ollama với
  HTTP mock) + 4 test CopilotPanel + 1 test E2E - tổng backend 49, frontend 30,
  E2E 11.
- Thêm đổi provider Copilot runtime: 4 test backend + 2 test CopilotPanel -
  tổng backend 53, frontend 32.
- Thêm kiểm tra khả dụng provider nhận dạng: 9 test backend (8 unit diagnostics
  + 1 API status) + 3 test Toolbar - tổng backend 62, frontend 35, E2E 11.

### Sắp tới
- Teacher Copilot nâng cao: chọn cấp học, custom model/LLM provider.
- Open Teaching Activity Platform - plugin, chia sẻ cộng đồng.
- Các loại hàm khác: phân thức, sin/cos, logarit, mũ.
- Tích hợp Recognition thực (Ollama + LLaVA/Qwen-VL, Pix2Text) thay Mock Provider.