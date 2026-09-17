# Changelog

Tất cả thay đổi đáng chú ý của dự án sẽ được ghi lại trong file này.

Định dạng dựa trên [Keep a Changelog](https://keepachangelog.com/vi/1.1.0/),
dự án tuân thủ [Semantic Versioning](https://semver.org/lang/vi/).

## [Chưa phát hành]

### Cải thiện độ tin cậy phát hành
- Khóa dependency Python bằng `backend/requirements.lock` và dùng lock trong CI,
  E2E, đóng gói Windows.
- Hợp nhất release workflow, tạo thêm gói portable ZIP, cố định phiên bản và
  checksum `uv`.
- Đồng bộ metadata phiên bản `1.0.0` và bổ sung notices cho runtime/build tools.

## [1.0.0] - 2026-09-15

### Đã thêm (Stage 1 - MVP)
- **Kiến thức liên quan có trích nguồn**: API `POST /api/knowledge/related` suy
  chủ đề từ Math Engine, chỉ gọi Wikipedia Việt/Anh và Wikibooks Anh qua
  allowlist, luôn có nội dung Việt tích hợp, timeout/giới hạn dung lượng/cache
  stale khi lỗi. Tab Kiến thức tự tải khi mở, cache IndexedDB, chuyển Tiếng
  Việt/Nguyên bản và hiển thị link nguồn, contributors, revision, giấy phép,
  trạng thái dịch cùng cảnh báo nội dung tham khảo.
- **Lời giải phổ thông chi tiết**: phương trình bậc nhất/bậc hai có bước xác
  định hệ số, biến đổi, biệt thức/công thức nghiệm và thế nghiệm; metadata bước
  vẫn tương thích response cũ và được frontend trình bày thành từng thẻ rõ ràng.
- **Nút AI cố định ở mép phải toolbar**: vùng công cụ có thể cuộn độc lập, nút
  trạng thái nhỏ luôn thấy; chi tiết provider mặc định ẩn, desktop dùng popover
  và mobile dùng panel sát đáy.
- **Frontend Blueprint responsive**: activity dùng tab Đồ thị/Lời giải/Gợi ý
  với một vùng cuộn duy nhất, hết đè nội dung; JSXGraph và Konva tự resize,
  zoom card đồng nhất, có nút zoom/reset, activity mới đặt lệch nhau, mobile có
  chế độ tập trung và nút thu nhỏ. Toolbar/board/modal được làm mới, hỗ trợ
  pointer/touch, focus rõ và lỗi API hiển thị ngay trong modal.
- **Nhận hàm viết đảo hai vế**: `2x+1=y` được chuẩn hóa thành `y=2x+1` ở cả
  frontend và backend, tạo cùng đồ thị; các phương trình `x+y=2`, `2x+1=5`
  vẫn đi đúng luồng giải.
- **AI quét được cả Text trên bảng**: vùng nhận dạng rasterize Text và nét bút
  theo đúng thứ tự, có nền trắng cho OCR; vùng rỗng báo rõ thay vì im lặng.
- **Tên biến đa dạng**: Math Engine, activity và Copilot bảo toàn biến nguồn/
  phụ thuộc như `z=2t+1`, `f(u)=u^2-1` thay vì bắt buộc `y=f(x)`.
- **Giải phương trình bậc nhất/bậc hai**: API `POST /api/math/solve`, tự phân
  loại sau OCR/nhập bàn phím, chọn ẩn cho `x+y=2`, trả nghiệm exact/gần đúng,
  các trường hợp suy biến, bước giải LaTeX và trạng thái kiểm chứng. Activity
  hàm bậc nhất/bậc hai có mục "Đáp án & lời giải"; phương trình có activity riêng.
- **Chuyển LaTeX OCR thành biểu thức đọc được**: `to_expression` giờ xử lý
  đầy đủ cú pháp LaTeX mà Pix2Text/Ollama trả về — `\frac{n}{d}` (kể cả phân
  số lồng), `x^{2}`, `\sqrt{x}`, `\sqrt[3]{x}`, `2\cdot 3^x`, `\left(...\right)`,
  `\log_{10}(x)` -> `log(x,10)`, `\lg(x)`, `\pi`. Trước đây ô "Biểu thức chuẩn
  hóa" hiện nguyên LaTeX `\frac{2 x+3}{x-1}` (không đọc được) và Xác nhận báo
  lỗi; nay hiện `(2 x+3)/(x-1)` và phân tích thành activity phân thức bình
  thường. Dán thẳng LaTeX vào ô nhập công thức cũng hoạt động.
- **Modal xác nhận nhận dạng**: kết quả LaTeX của OCR ("Nhận dạng (độ tin
  cậy X%)") được render bằng KaTeX thay vì hiển thị văn bản thô.
- **Nhận đa dạng cách viết biểu thức**: tầng tiền xử lý `_preprocess_input`
  nhận thêm ngoặc nhọn LaTeX/OCR (`3^{x}`, `2*3**{x}-1`), số mũ Unicode
  (`x²-4x+3`, `x⁻¹`), ký hiệu phép toán (`·` `×` `÷` -> `*` `/`), và các cách
  viết logarit: `lg(x)`/`log10(x)` = cơ số 10, `log2(x)`/`log₂(x)` = cơ số 2,
  `loge(x)` = ln; `log(x)` không ghi cơ số vẫn là ln (khớp SymPy). Biểu thức
  có hệ số là ký tự (`a*3^x`) vẫn báo lỗi rõ ràng.
- **Mở rộng Math Engine thêm 4 loại hàm**: hàm phân thức `(ax+b)/(cx+d)`,
  lượng giác `a*sin(bx+c)+d` / `a*cos(bx+c)+d`, mũ `a*b^x+c` và logarit
  `a*log(x,base)+c`. API `/api/math/analyze` trả thêm `RationalFeatures`,
  `TrigFeatures`, `ExponentialFeatures`, `LogarithmicFeatures`; `/api/math/activity`
  tạo activity loại `rational_function` / `trig_function` /
  `exponential_function` / `logarithmic_function` kèm chuỗi bước giảng dạy
  (tiệm cận, đường trung bình, nghiệm...). Biểu thức ngoài chuẩn tắc
  (`tan(x)`, tích các hàm...) báo lỗi rõ ràng thay vì sinh activity sai.
- **Frontend: shell `ActivityCanvas` dùng chung cho mọi activity**: nút hiện/ẩn
  đặc trưng (tiệm cận đứng/ngang, nghiệm, đường trung bình, max/min...), slider
  hệ số, điều hướng bước giảng dạy, công thức KaTeX; 4 widget mới
  (phân thức, lượng giác, mũ, logarit) đăng ký qua `activityRegistry`.
  Slider giữ giá trị hợp lệ (chống chia 0, log x≤0, cơ số ≤0, |b|→0).
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

### Thay đổi
- **Bỏ 3 tác vụ Windows Task Scheduler tự khởi động** (`MathBackend`,
  `P2TServe`, `P2TWatchdog` — trigger đăng nhập + watchdog poll mỗi 2 phút):
  backend và Pix2Text giờ chỉ chạy khi người dùng gọi lệnh, qua các script mới
  trong `scripts/` — `backend-start.ps1` (bật backend + Pix2Text; watcher ẩn
  theo dõi tiến trình uvicorn và **tự tắt Pix2Text ngay khi backend dừng**,
  không poll), `backend-stop.ps1`, `p2t-start.ps1`, `p2t-stop.ps1`. Đường dẫn
  máy cá nhân được suy tương đối từ vị trí repo nên script dùng được trên máy khác.

### Đã sửa
- **File `.env` giờ được đọc thật**: thêm `python-dotenv` + `load_dotenv()` trong `main.py` (trước import app.\*) → `backend/.env` (gitignored, cục bộ mỗi máy) xác định `RECOGNITION_PROVIDER` mặc định lúc khởi động; test dùng `conftest.py` đặt mock để CI ổn định.

### Đã sửa (Stage 1)
- Sửa JSXGraph co khoảng 2px mỗi vòng rồi biến mất: `ResizeObserver` không còn
  để JSXGraph ghi ngược width/height lên container `border-box`; thêm hồi quy
  cho resize, StrictMode cleanup, chuyển tab và kích thước ổn định.
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
