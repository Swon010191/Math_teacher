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
  bước xác nhận/sửa của giáo viên (Stage 1 dùng Mock Provider).
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

## Cài đặt & chạy (từ mã nguồn)

> Chi tiết xem [Hướng dẫn cài đặt](docs/HUONG_DAN_CAI_DAT.md).

### 1. Lấy mã nguồn

```bash
git clone https://github.com/Swon010191/Math_teacher.git
cd Math_teacher
```

### 2. Khởi động backend (Math Engine)

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/macOS
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Khởi động frontend (AI Whiteboard)

```bash
cd frontend
npm install
npm run dev
```

Mở trình duyệt: **http://localhost:5173**

## Hướng dẫn sử dụng

### Màn hình chính

Thanh công cụ gồm 3 nhóm:

| Nhóm | Nút | Chức năng |
|---|---|---|
| Công cụ vẽ | **Di chuyển** | Nhấn và kéo để dời bảng sang vị trí khác (hoặc giữ chuột giữa ở mọi chế độ) |
| | **Chọn** | **Khoanh vùng** để chọn nhiều đối tượng, rồi kéo để di chuyển cùng nhau; bấm vào đối tượng để chọn 1 |
| | **Bút** | Vẽ nét tự do bằng chuột/stylus |
| | **Text** | Thêm chữ vào bảng (bấm vào vị trí muốn đặt) |
| | **AI** | Khoanh vùng nét vẽ để nhận dạng công thức |
| | **Xóa** | **Khoanh vùng** để xóa toàn bộ đối tượng bên trong; bấm vào đối tượng để xóa 1 |
| Bảng | **Công thức** | Nhập công thức bằng bàn phím (phương án dự phòng) |
| | **Lưu / Mở** | Lưu bảng trên máy (IndexedDB) / mở bảng đã lưu |
| Dữ liệu | **Xuất / Nhập JSON** | Sao lưu, chia sẻ hoặc phục hồi toàn bộ bảng |
| | **Xóa bảng** | Xóa toàn bộ nội dung bảng |

**Thao tác chung:** lăn chuột để phóng to/thu nhỏ · **Di chuyển** để kéo dời bảng
(hoặc giữ chuột giữa ở mọi chế độ).

> **Trạng thái AI:** góc phải thanh công cụ có đèn xanh/đỏ cho biết máy chủ AI
> đã kết nối chưa. **Bấm vào "AI sẵn sàng"** để xem và đổi provider nhận dạng
> đang dùng (Mock/Ollama Vision/Pix2Text) ngay trong lúc chạy. Popover còn hiển
> thị **trạng thái khả dụng của từng provider** (✓ xanh / ✗ đỏ kèm hướng dẫn cài
> đặt nếu chưa có) và nút **"Kiểm tra lại"** để ping lại các dịch vụ. Khi đèn đỏ,
> hãy khởi động backend: `uvicorn app.main:app --port 8000` (thư mục `backend/`).

**Recognition thật (tùy chọn):** mặc định dùng Mock (demo không cần cài gì).
Muốn nhận dạng thật, cài Ollama hoặc Pix2Text rồi đặt biến môi trường trong
`backend/.env` (xem `backend/.env.example`):

| Provider | Cài đặt | Cấu hình |
|---|---|---|
| `ollama_vision` | Cài [Ollama](https://ollama.com) rồi `ollama pull llava` (hoặc Qwen-VL); đảm bảo `ollama serve` đang chạy | `RECOGNITION_PROVIDER=ollama_vision`, `OLLAMA_URL`, `OLLAMA_MODEL` |
| `pix2text` | `pip install pix2text[serve]` rồi chạy `p2t serve` | `RECOGNITION_PROVIDER=pix2text`, `PIX2TEXT_URL` |

#### Hướng dẫn cài đặt chi tiết (khuyến nghị, dựa trên máy Windows)

> Cả hai dịch vụ được cài **trong thư mục `ai-tools/` của dự án** — dành riêng cho
> máy cá nhân, **không được đẩy lên git** (đã nằm ngoài vùng theo dõi). Khi tải mã
> nguồn mới về, bạn phải cài lại các bước dưới đây.

**1. Ollama Vision** (nhận dạng bằng LLM thị giác `llava`)

```powershell
# Tải bản portable: https://ollama.com/download/windows → giải nén vào ai-tools\ollama
# Đặt biến môi trường OLLAMA_MODELS trỏ tới thư mục chứa model (máy này dùng D:\Misc\Tools\AI_Models)
ollama pull llava       # model thị giác (≈ 4.7 GB)
ollama pull llama3.2    # model chat cho Teacher Copilot (≈ 2.0 GB)
ollama serve            # chạy server tại http://localhost:11434
```

> Lưu ý: `ollama pull` là lệnh *client* — model được lưu vào thư mục của **server**
> đang chạy (theo biến `OLLAMA_MODELS` của server), không phải nơi bạn gõ lệnh.
> Đảm bảo `OLLAMA_MODELS` trỏ đúng thư mục chứa model trước khi pull/serve.

**2. Pix2Text** (nhận dạng công thức chuyên dụng)

```powershell
cd ai-tools\pix2text
py -3.14 -m venv .venv
.venv\Scripts\python -m pip install -U pip pix2text[serve]   # tự tải các model MFD/MFR về
# Đặt biến môi trường (máy này đã đặt): PIX2TEXT_HOME=<project>\ai-tools\pix2text\.pix2text
.venv\Scripts\p2t.exe serve --port 8503       # chạy server tại http://localhost:8503
```

**3. Khởi động lại sau khi tắt máy:** chỉ cần chạy lại 2 lệnh `ollama serve` và
`p2t serve --port 8503` ở trên (máy này đã tạo 2 tác vụ Windows **Task Scheduler**
`P2TServe` và `MathBackend` với trigger đăng nhập — **tự khởi động khi đăng nhập**
cùng với Ollama Desktop). Khi backend chạy rồi, mở giao diện và bấm
**"AI sẵn sàng"** → popover liệt kê 3 provider (Mock / Ollama Vision / Pix2Text),
bấm **"Kiểm tra lại"** để ping lại dịch vụ; provider nào xanh ✓ là sẵn sàng dùng được.

> **Nhận dạng thật có thể chậm:** model AI chạy local trên CPU mất **khoảng 10–60
> giây** cho lần đầu (llava 7B). Hệ thống chờ tối đa **120 giây**; trong lúc chờ
> giao diện hiển thị trạng thái đang xử lý, không bị cắt giữa chừng như trước.

**Teacher Copilot:** mặc định dùng `rule_based` (nội dung sinh theo quy tắc,
không cần AI). Muốn dùng LLM local, cài [Ollama](https://ollama.com) + `ollama
pull llama3.2`, rồi đặt `COPILOT_PROVIDER=ollama` (tùy chọn
`OLLAMA_MODEL_COPILOT`) trong `backend/.env`.

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
2. Nhập biểu thức (hỗ trợ `x^2`, `4x`, `x**2`, `sin(x)`, `(2x+1)/(x-1)`,
   `2^x`, `log(x,10)`...), ví dụ `x^2 - 4x + 3`, bấm Enter.
3. Activity tương ứng xuất hiện trên bảng (hàm bậc hai, bậc nhất, phân thức,
   lượng giác `sin/cos`, mũ, logarit) — mỗi loại có slider hệ số và bộ nút
   hiện/ẩn đặc trưng (tiệm cận, nghiệm, đường trung bình...).

### Mẹo giảng dạy

- **Hỏi trước, tiết lộ sau:** hỏi học sinh dự đoán đỉnh/trục đối xứng, sau đó
  bấm nút hiện đáp án.
- **Khám phá hệ số:** kéo slider `a` để học sinh thấy bề lõm và độ hẹp/rộng
  của parabol thay đổi; giữ nguyên `b`, `c` để so sánh.
- **Tắt AI vẫn dùng được:** mọi tính năng toán học và bảng vẽ hoạt động độc lập
  với Generative AI — không cần tài khoản, không cần API key.

## Kiểm thử

```bash
# Backend (87 test)
cd backend
pytest

# Frontend (62 test đơn vị)
cd frontend
npm test

# E2E (13 test luồng chính — tự khởi động backend + frontend)
cd frontend
npm run test:e2e
```

Trên máy Windows, nếu backend chưa được cài venv tại `backend/.venv`, chỉ định
đường dẫn Python cho Playwright bằng biến môi trường `BACKEND_PYTHON`
(ví dụ `BACKEND_PYTHON=C:\path\to\python.exe npm run test:e2e`).

Mỗi lần push lên `main` hoặc mở PR, [GitHub Actions](.github/workflows/ci.yml)
tự chạy toàn bộ test ở trên. Push tag `v*` sẽ tự tạo GitHub Release.

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
└── .github/              # Issue templates, CI
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