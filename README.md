# AI Teaching Assistant - Math Teacher

![CI](https://github.com/Swon010191/Math_teacher/actions/workflows/ci.yml/badge.svg)

Nền tảng giảng dạy AI mã nguồn mở giúp giáo viên biến nội dung trên bảng thành
trải nghiệm giảng dạy trực quan, tương tác và **do giáo viên kiểm soát**.

> Dự án này không phải chatbot đặt cạnh bảng. Điểm khác biệt là biến nội dung
> trên bảng thành các **hoạt động giảng dạy tương tác** (đồ thị, slider, tiết lộ
> đáp án theo từng bước) ngay trên chính chiếc bảng điện tử.

## Tính năng chính

- **AI Whiteboard (B)** — Bảng điện tử để viết, vẽ, chọn, sắp xếp toàn bộ bài giảng.
- **Interactive Teaching Canvas (A)** — Khối nội dung tương tác (đồ thị, slider,
  nút hiện/ẩn đáp án, chuỗi bước giảng dạy) nằm ngay trên bảng.
- **Recognition Engine** — Nhận dạng nét viết tay thành công thức toán học, kèm
  bước xác nhận/sửa của giáo viên; hỗ trợ Mock, Ollama Vision và Pix2Text.
- **Giải phương trình** — Tự động nhận dạng phương trình bậc nhất/bậc hai, cho
  chọn ẩn khi có nhiều biến, hiển thị đáp án chính xác, các bước giải phổ thông
  chi tiết và phép thế nghiệm kiểm chứng.
- **Kiến thức có trích nguồn** — Tab kiến thức liên quan tự tải nội dung từ kho
  tích hợp, Wikipedia/Wikibooks, có chuyển Tiếng Việt/Nguyên bản, tác giả,
  revision, giấy phép, cache ngoại tuyến và cảnh báo nội dung tham khảo.
- **Teacher Copilot (D)** — AI đề xuất nội dung giảng dạy (tóm tắt, câu hỏi gợi
  mở, ví dụ, chuỗi bước) cho từng hoạt động; giáo viên duyệt trước khi lên
  bảng; chạy local, không bắt buộc API key.
- **Open Teaching Activity (C)** *(giai đoạn sau)* — Định dạng JSON mở để lưu,
  chia sẻ và mở rộng hoạt động giảng dạy.

## Yêu cầu hệ thống

| Công cụ | Phiên bản tối thiểu |
|---|---|
| Node.js | 20+ |
| npm | 10+ |
| Python | 3.11+ |
| pip | 23+ |
| Git | 2.40+ |

## Cài đặt 1 lần (ứng dụng)

Tải file `Setup-AI-Teaching-Assistant-1.0.0.exe` trong mục Release rồi Next → Finish, không cần quyền admin, không cần cài Node/Python:

- Mở app từ Desktop/Start Menu → backend + web tự chạy, trình duyệt tự mở.
- Tick **Pix2Text** lúc cài để có nhận dạng công thức thật (tải ~1-2 GB,
  cần mạng, mất 10-30 phút). Bỏ tick thì app dùng Mock, mọi tính năng
  toán + bảng vẽ vẫn chạy, có thể cài AI sau bằng cách chạy lại Setup.
- Muốn dùng Ollama Vision/Copilot LLM thì tự cài Ollama rồi đổi provider
  trên popover AI của app.
- Gỡ: Windows Settings → Apps → Uninstall (app đang chạy sẽ được nhắc tắt).

> **Tự build bộ cài** từ mã nguồn: `powershell -ExecutionPolicy Bypass -File packaging\build.ps1`
> (cần Node 20+, Python 3.11+, Inno Setup; ra file `packaging/output/Setup-*.exe`).

## Cài đặt & chạy (từ mã nguồn)

> Chi tiết xem [Hướng dẫn cài đặt](docs/HUONG_DAN_CAI_DAT.md).

### 1. Lấy mã nguồn

```bash
git clone https://github.com/Swon010191/Math_teacher.git
cd Math_teacher
```

### 2. Khởi động backend + Pix2Text (Windows, khuyến nghị)

```powershell
# Từ thư mục gốc dự án
powershell -ExecutionPolicy Bypass -File scripts\backend-start.ps1
```

- Bật backend (`uvicorn --reload`, cửa sổ riêng) + tự bật Pix2Text kèm theo
- Tắt: **Ctrl+C** ở cửa sổ backend → Pix2Text tự tắt ngay (watcher)
- File `backend/.env` (gitignored) quyết định provider mặc định: `RECOGNITION_PROVIDER=pix2text|ollama_vision|mock`

> **Nâng cao (Linux/macOS / thủ công):**
> ```bash
> cd backend && python -m venv .venv && source .venv/bin/activate
> pip install -r requirements.txt
> uvicorn app.main:app --reload --port 8000
> # Pix2Text chạy riêng nếu cần: scripts\p2t-start.ps1
> ```

### 3. Khởi động frontend (AI Whiteboard)

```bash
cd frontend
npm install
npm run dev
```

Mở trình duyệt: **http://localhost:5173**

### 4. Cài đặt AI nhận dạng & Copilot (tùy chọn)

Mặc định dùng Mock Provider (không cần cài gì). Muốn nhận dạng thật (Pix2Text/Ollama Vision) hoặc Copilot AI, cài các dịch vụ dưới đây rồi cấu hình qua `backend/.env` (xem `backend/.env.example`) hoặc đổi lúc chạy trên UI.

| Provider | Cài đặt | Cấu hình |
|---|---|---|
| `ollama_vision` | Cài [Ollama](https://ollama.com) rồi `ollama pull llava` (hoặc Qwen-VL); đảm bảo `ollama serve` đang chạy | `RECOGNITION_PROVIDER=ollama_vision`, `OLLAMA_URL`, `OLLAMA_MODEL` |
| `pix2text` | `pip install pix2text[serve]` rồi chạy `p2t serve` (hoặc `scripts\p2t-start.ps1`) | `RECOGNITION_PROVIDER=pix2text`, `PIX2TEXT_URL` |

#### Hướng dẫn cài đặt chi tiết (khuyến nghị, dựa trên máy Windows)

> Cả hai dịch vụ được cài **trong thư mục `ai-tools/` của dự án** — dành riêng cho máy cá nhân, **không được đẩy lên git** (đã nằm ngoài vùng theo dõi). Khi tải mã nguồn mới về, bạn phải cài lại các bước dưới đây.

**1. Ollama Vision** (nhận dạng bằng LLM thị giác `llava`)

```powershell
# Tải bản portable: https://ollama.com/download/windows → giải nén vào ai-tools\ollama
# Đặt biến môi trường OLLAMA_MODELS trỏ tới thư mục chứa model (máy này dùng D:\Misc\Tools\AI_Models)
ollama pull llava       # model thị giác (≈ 4.7 GB)
ollama pull llama3.2    # model chat cho Teacher Copilot (≈ 2.0 GB)
ollama serve            # chạy server tại http://localhost:11434
```

> Lưu ý: `ollama pull` là lệnh *client* — model được lưu vào thư mục của **server** đang chạy (theo biến `OLLAMA_MODELS` của server), không phải nơi bạn gõ lệnh. Đảm bảo `OLLAMA_MODELS` trỏ đúng thư mục chứa model trước khi pull/serve.

**2. Pix2Text** (nhận dạng công thức chuyên dụng)

```powershell
cd ai-tools\pix2text
py -3.14 -m venv .venv
.venv\Scripts\python -m pip install -U pip pix2text[serve]   # tự tải các model MFD/MFR về
# Đặt biến môi trường (máy này đã đặt): PIX2TEXT_HOME=<project>\ai-tools\pix2text\.pix2text
.venv\Scripts\p2t.exe serve --port 8503       # chạy server tại http://localhost:8503
```

**Teacher Copilot:** mặc định dùng `rule_based` (nội dung sinh theo quy tắc, không cần AI). Muốn dùng LLM local, cài [Ollama](https://ollama.com) + `ollama pull llama3.2`, rồi đặt `COPILOT_PROVIDER=ollama` (tùy chọn `OLLAMA_MODEL_COPILOT`) trong `backend/.env`.

> **Nhận dạng thật có thể chậm:** model AI chạy local trên CPU mất **khoảng 10–60 giây** cho lần đầu (llava 7B). Hệ thống chờ tối đa **120 giây**; trong lúc chờ giao diện hiển thị trạng thái đang xử lý, không bị cắt giữa chừng như trước.

## Hướng dẫn sử dụng

### Màn hình chính

Thanh công cụ gồm 3 nhóm:

| Nhóm | Nút | Chức năng |
|---|---|---|
| Công cụ vẽ | **Di chuyển** | Nhấn và kéo để dời bảng sang vị trí khác (hoặc giữ chuột giữa ở mọi chế độ) |
| | **Chọn** | **Khoanh vùng** để chọn nhiều đối tượng, rồi kéo để di chuyển cùng nhau; bấm vào đối tượng để chọn 1 |
| | **Bút** | Vẽ nét tự do bằng chuột/stylus |
| | **Văn bản** | Thêm chữ vào bảng (bấm vào vị trí muốn đặt) |
| | **Nhận dạng** | Khoanh vùng nét vẽ hoặc nội dung Văn bản để nhận dạng công thức/phương trình |
| | **Tẩy vùng** | **Khoanh vùng** để xóa toàn bộ đối tượng bên trong; bấm vào đối tượng để xóa 1 |
| Bảng | **Công thức** | Nhập công thức bằng bàn phím (phương án dự phòng) |
| | **Lưu / Mở** | Lưu bảng trên máy (IndexedDB) / mở bảng đã lưu |
| Dữ liệu | **Xuất / Nhập JSON** | Sao lưu, chia sẻ hoặc phục hồi toàn bộ bảng |
| | **Xóa bảng** | Xóa toàn bộ nội dung bảng |

**Thao tác chung:** lăn chuột hoặc dùng cụm nút góc dưới để phóng to/thu nhỏ ·
**Di chuyển** để kéo dời bảng (hoặc giữ chuột giữa ở mọi chế độ). Activity có
bốn tab **Đồ thị / Lời giải / Kiến thức / Gợi ý** khi nội dung tương ứng khả
dụng, chỉ hiển thị một vùng nội dung mỗi lúc để không bị chồng lên nhau. Trên
mobile, chọn activity để mở chế độ tập trung.

> **Trạng thái AI:** góc phải thanh công cụ có đèn xanh/đỏ cho biết máy chủ AI
> đã kết nối chưa. Nút **AI** luôn nằm ở mép phải, không cuộn theo các công cụ;
> bấm nút để xem và đổi provider nhận dạng
> đang dùng (Mock/Ollama Vision/Pix2Text) ngay trong lúc chạy. Popover còn hiển
> thị **trạng thái khả dụng của từng provider** (✓ xanh / ✗ đỏ kèm hướng dẫn cài
> đặt nếu chưa có) và nút **"Kiểm tra lại"** để ping lại các dịch vụ. Khi đèn đỏ,
> hãy khởi động backend: `uvicorn app.main:app --port 8000` (thư mục `backend/`).

> **Recognition thật / Teacher Copilot:** mặc định dùng Mock + rule_based (không cần cài gì).
> Muốn nhận dạng thật hoặc Copilot AI, xem chi tiết cài đặt ở
> [Cài đặt & chạy — bước 4](#4-cài-đặt-ai-nhận-dạng--copilot-tùy-chọn).
> Sau khi cài, bấm **"AI sẵn sàng"** → popover liệt kê 3 provider, bấm **"Kiểm tra lại"** để ping.

> **Trình tự gợi ý giảng dạy:** mở activity → bấm **💡 Gợi ý** → chọn **Nguồn
> gợi ý** (Gợi ý có sẵn / Ollama AI local) nếu muốn đổi → xem đề xuất (chỉ là
> gợi ý, số liệu đến từ Math Engine) → bấm **Đưa lên bảng** để duyệt; gợi ý
> xuất hiện ngay trong activity và được lưu cùng bảng.

> **Chọn / Xóa theo khoanh vùng:** không cần bấm trúng đối tượng — chỉ cần kéo
> một khung bao quanh vùng muốn chọn hoặc muốn xóa. Kết quả hiển thị ngay.

### Luồng chính 1 — Viết tay → Nhận dạng → Activity (được khuyến nghị)

1. Bấm **Bút** và viết công thức lên bảng, ví dụ `y = x^2 - 4x + 3`.
2. Bấm **AI**, sau đó **khoanh vùng** bao quanh công thức vừa viết.
3. Hệ thống nhận dạng (Mock Provider) và hiện hộp **Xác nhận công thức**:
    - Xem kết quả LaTeX và biểu thức chuẩn hóa.
    - Xem hệ thống tự phân loại **Phân tích hàm số** hoặc **Giải phương trình**.
    - Chọn ẩn cần giải nếu phương trình có nhiều biến.
    - **Sửa nếu nhận dạng sai**, rồi bấm **Xác nhận và tạo activity**.
4. Một **hoạt động giảng dạy** xuất hiện ngay tại vị trí vùng khoanh:
   - Đồ thị parabol tương tác (JSXGraph).
   - Slider `a`, `b`, `c` — kéo để quan sát đồ thị thay đổi.
   - Nút **Hiện đỉnh / Hiện nghiệm / Hiện trục** — tiết lộ đáp án theo ý giáo viên.
   - **Bước trước / Bước tiếp** — điều hướng chuỗi giảng dạy từng bước.
5. Kéo thanh tiêu đề để di chuyển, kéo góc dưới phải để đổi kích thước, bấm
   **×** (hoặc dùng công cụ Xóa) để xóa khối.

### Luồng chính 2 — Gõ công thức (dự phòng)

1. Bấm **Công thức**.
2. Nhập biểu thức (hỗ trợ nhiều dạng viết: `x^2`, `4x`, `x**2`, `x²`,
    `sin(x)`, `(2x+1)/(x-1)`, `2^x`, `3^{x}`, `2·3^x`, `log(x,10)`,
    `lg(x)`, `log10(x)`, `log2(x)`, `ln(x)`; dán thẳng LaTeX cũng được —
    `\frac{2x+3}{x-1}`, `x^{2}`, `\sqrt{x}`, `2\cdot 3^x`...), ví dụ
    `x^2 - 4x + 3`, bấm Enter.
3. Có thể dùng tên biến khác, ví dụ `z=2t+1`, hoặc nhập phương trình như
   `2u+3=9`, `x+y=2`. Hai cách viết `2x+1=y` và `y=2x+1` được hiểu là cùng
   một hàm số và đều tạo đồ thị.
4. Xác nhận phân loại tự động; nếu có nhiều biến, chọn biến cần giải.
5. Activity tương ứng xuất hiện trên bảng (hàm bậc hai, bậc nhất, phân thức,
    lượng giác `sin/cos`, mũ, logarit) — mỗi loại có slider hệ số và bộ nút
   hiện/ẩn đặc trưng. Hàm bậc nhất/bậc hai có thêm mục **Đáp án & lời giải**;
   phương trình có activity lời giải riêng.

### Mẹo giảng dạy

- **Hỏi trước, tiết lộ sau:** hỏi học sinh dự đoán đỉnh/trục đối xứng, sau đó
  bấm nút hiện đáp án.
- **Khám phá hệ số:** kéo slider `a` để học sinh thấy bề lõm và độ hẹp/rộng
  của parabol thay đổi; giữ nguyên `b`, `c` để so sánh.
- **Tắt AI vẫn dùng được:** mọi tính năng toán học và bảng vẽ hoạt động độc lập
  với Generative AI — không cần tài khoản, không cần API key.

## Kiểm thử

```bash
# Backend (258 test)
cd backend
pytest

# Frontend (119 test đơn vị)
cd frontend
npm test

# E2E (21 test luồng chính — tự khởi động backend + frontend)
cd frontend
npm run test:e2e
```

Trên máy Windows, nếu backend chưa được cài venv tại `backend/.venv`, chỉ định
đường dẫn Python cho Playwright bằng biến môi trường `BACKEND_PYTHON`
(ví dụ `BACKEND_PYTHON=C:\path\to\python.exe npm run test:e2e`).

Mỗi lần push lên `main` hoặc mở PR, [GitHub Actions](.github/workflows/ci.yml)
tự chạy toàn bộ test ở trên. Push tag `v*` sẽ tự tạo GitHub Release.

## Những thay đổi

> Toàn bộ lịch sử chi tiết xem tại [CHANGELOG.md](CHANGELOG.md). Dưới đây là tóm tắt
> những thay đổi chính so với phiên bản trước.

### Gói ứng dụng — Setup.exe (mới)
| Trước | Sau |
|---|---|
| Phải cài Node + Python + tự chạy backend/frontend | **1 file** `Setup-AI-Teaching-Assistant-1.0.0.exe` (57MB) — Next → Finish là dùng |
| Cần quyền admin / cấu hình thủ công | Cài per-user, không cần admin; backend + web tự chạy, trình duyệt tự mở |
| Pix2Text/Ollama phải tự cài | Tick **Pix2Text** lúc cài để tự tải (~1–2 GB); bỏ tick thì dùng Mock, cài lại sau được |
| Gỡ thủ công | Gỡ qua Windows Settings → Apps |

- Đóng gói bằng [PyInstaller](https://pyinstaller.org/) + [Inno Setup](https://jrsoftware.org/isinfo.php) (`packaging/app.iss`, `packaging/build.ps1`, `packaging/server_main.py`, `packaging/launcher.py`)
- Gỡ sạch sẽ; CI tự build Setup trên `windows-latest` khi push tag `v*` (`.github/workflows/package.yml`)

### Backend — ổn định & bảo mật
- **Parser công thức** xử lý đúng các dạng lồng nhau: `log10(sin(x)+1)`, `lg((x+1)*2)`, `log_{10}(x)`, `2·3^{x}`, `x²`, `\frac{...}{...}` lồng nhau; hỗ trợ nhiều tên biến (`z=2t+1`, `f(u)=...`) và tự phát hiện biến khi có nhiều biến
- **Validate chặt hơn**: chặn tên vô nghĩa (`abc` → 400), cho phép `_`/`'`/`"` trong tên biến, validate `confidence`/`results` kiểu đúng trước khi đọc
- **Provider an toàn hơn**: đóng HTTP client sau mỗi request (tránh rò socket), thêm `close()` cho mọi provider
- **API**: ẩn URL nội bộ trong lỗi (`_redact_urls`), CORS đọc từ env `CORS_ORIGINS`, thêm `StaticFiles` + SPA fallback để chạy 1-port trong bản đóng gói
- **Hạ tầng**: `.gitignore` thêm `ai-tools/` `.pix2text/` `*.onnx`; `conftest.py` cô lập env cho CI; `requirements.txt` thêm `python-multipart`

### Frontend — sửa lỗi & mobile
- **Kết nối**: `BASE_URL` chuẩn hóa (trim, xóa `/` cuối), `checkHealth` có timeout, `AbortSignal.timeout` fallback, fix `...init` spread
- **Bảng vẽ**: cap ảnh chụp 1600px, `pixelRatio` theo scale; marquee ngưỡng chia theo zoom; **pinch-zoom 2 ngón** trên mobile; cleanup `pointercancel`; chặn cuộn khi giữ chuột giữa
- **Import/Export**: validate JSON tối đa 5MB, dọn activity mồ côi khi import; fix Safari `appendChild` → `click`+`remove`
- **Nhập liệu**: thay `window.prompt` (bị chặn trên iOS) bằng modal; `formatNum(undefined)` → `'?'`
- **Activity**: cleanup listener bằng `useRef` + `pointercancel`; hiện "chưa hỗ trợ" khi không có tab; preview `x**2` → `x²` cho KaTeX
- **Chống race**: `CopilotPanel` dùng `AbortController` + `alive` flag; `Toolbar` dùng `providerChangeVersionRef`; `KnowledgeActivity` abort khi unmount
- **Khác**: `appStore` dùng `crypto.randomUUID()`, nhớ tool đã chọn; `classifyMathInput` nhận `==`/`>=`/`<=`/`!=` là `solve`; `knowledgeTypes` chấp nhận link `http:`
- **UX polish**: nhớ tool đã chọn, marquee theo scale, map lỗi Anh→Việt, fallback card cho activity lạ

### Kiểm thử — tăng độ phủ
- **Backend**: +13 test (`log` ngoặc lồng, normalize nhiều biến, tên vô nghĩa, provider cùng cấp) → **258 tests**
- **Frontend**: +11 test (`boardValidation`, `classifyMathInput` mở rộng) → **119 tests**
- **E2E**: cập nhật theo flow modal mới, fix strict-mode → **21/21 passed**

### Script & Docs
- `scripts/_common.ps1` đổi port qua env, `Stop-P2T` chỉ giết Pix2Text; `backend-start.ps1` kiểm tra `/health` khi port bận
- `.env.example` thêm `CORS_ORIGINS`
- `packaging/` đầy đủ + CI build Setup; README cập nhật số test & hướng dẫn cài

## Cấu trúc repository

```
├── documents/            # Tài liệu kế hoạch & yêu cầu (BA)
├── docs/                 # Tài liệu kỹ thuật & hướng dẫn
├── backend/              # FastAPI + SymPy (Math Engine, Recognition)
│   ├── app/
│   │   ├── api/          # REST endpoints
│   │   ├── domain/       # Mô hình miền
│   │   ├── services/     # Math Service, Recognition Service
│   │   ├── providers/    # RecognitionProvider (Mock → Ollama → Pix2Text)
│   │   └── schemas/      # Pydantic schemas
│   └── tests/
├── frontend/             # React + Vite + TypeScript
│   └── src/
│       ├── features/
│       │   ├── board/        # AI Whiteboard
│       │   ├── activities/   # Teaching Canvas + Activity Model
│       │   ├── recognition/  # Nhận dạng nét vẽ + xác nhận
│       │   ├── math/         # Giao tiếp Math Engine
│       │   └── copilot/      # Teacher Copilot (giai đoạn sau)
│       ├── components/
│       ├── providers/
│       ├── stores/           # Zustand
│       └── api/
├── examples/activities/  # File activity mẫu (JSON)
├── scripts/                # Script khởi động/tắt backend + Pix2Text (PowerShell)
├── packaging/              # Build Setup.exe (PyInstaller + Inno Setup)
└── .github/              # Issue templates, CI, GitHub Release
```

## Kiến trúc tổng quan

```
                          B - AI WHITEBOARD
                                   |
              +--------------------+--------------------+
              |                    |                    |
     A - Teaching Canvas   D - Teacher Copilot   C - Open Platform
        Chức năng cốt lõi      Trợ lý tùy chọn       Mở rộng tương lai
```

Nguyên tắc cốt lõi:

- **Math Engine (SymPy) là nguồn sự thật toán học** — LLM không được dùng để
  tính nghiệm, đạo hàm hay kết luận đáp án.
- LLM chỉ đề xuất nội dung sư phạm; đầu ra là JSON có schema, được validate, và
  **giáo viên phải duyệt trước khi lên bảng**.
- Local-first: không cần tài khoản, không cần cloud API, chạy offline.
- Khi AI lỗi/tắt, Math Core và Whiteboard vẫn hoạt động bình thường.

## Tài liệu

- [Yêu cầu dự án (tiếng Việt)](documents/AI_Teaching_Assistant_Tong_Hop.txt)
- [Kế hoạch BA](documents/BA_KE_HOACH.md)
- [Yêu cầu chi tiết](documents/REQUIREMENTS.md)
- [Kiến trúc hệ thống](documents/KIEN_TRUC.md)
- [Hướng dẫn cài đặt](docs/HUONG_DAN_CAI_DAT.md)
- [Báo cáo lỗi & đề xuất tính năng](.github/ISSUE_TEMPLATE/)
- [Lịch sử thay đổi](CHANGELOG.md)

## Đóng góp

Xem [CONTRIBUTING.md](CONTRIBUTING.md) và
[Thông tin thư viện & giấy phép](THIRD_PARTY_NOTICES.md).

## Giấy phép

Dự án phát hành theo giấy phép [MIT](LICENSE).
