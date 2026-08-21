# Hướng dẫn cài đặt từ mã nguồn

Hướng dẫn này mô tả cách cài đặt, biên dịch và chạy dự án **AI Teaching Assistant**
từ mã nguồn trên máy local. Dự án không yêu cầu tài khoản, cloud API hay API key.

## Yêu cầu hệ thống

| Công cụ | Phiên bản tối thiểu | Kiểm tra |
|---|---|---|
| Node.js | 20+ | `node --version` |
| npm | 10+ | `npm --version` |
| Python | 3.11+ | `python --version` |
| pip | 23+ | `pip --version` |
| Git | 2.40+ | `git --version` |

## Bước 1 - Lấy mã nguồn

```bash
git clone https://github.com/Swon010191/Math_teacher.git
cd Math_teacher
```

## Bước 2 - Cài đặt backend (Math Engine)

```bash
cd backend

# Tạo môi trường ảo
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/macOS
# source .venv/bin/activate

# Cài dependency
pip install -r requirements.txt

# Chạy server
uvicorn app.main:app --reload --port 8000
```

> Trên Windows, sau khi cài đặt xong (kể cả Pix2Text ở phần AI bên dưới) có thể
> dùng script tiện lợi `scripts\backend-start.ps1` — bật backend + Pix2Text
> trong 1 lệnh, tắt backend là Pix2Text tự tắt theo. Xem README mục
> **Khởi động hằng ngày**.

Kiểm tra:

- OpenAPI docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health
- Test API toán: `POST /api/math/analyze` với body `{"expression": "x**2 - 4*x + 3"}`

## Bước 3 - Cài đặt frontend (AI Whiteboard)

```bash
cd frontend
npm install
npm run dev
```

Mở trình duyệt: http://localhost:5173

## Bước 4 - Chạy kiểm thử

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## Bước 5 - Build production

```bash
cd frontend
npm run build
```

Bản build nằm trong `frontend/dist/`.

## Cấu hình AI (tùy chọn, giai đoạn sau)

Stage 1 sử dụng **Mock Recognition Provider** (không cần cấu hình gì thêm).

Khi tích hợp Recognition thật (Vision/Math OCR):

1. Cài [Ollama](https://ollama.com) (giấy phép MIT).
2. Tải model vision: `ollama pull llava` (hoặc qwen2.5-vl).
3. Cấu hình provider qua biến môi trường trong `backend/.env`
   (xem `backend/.env.example`).

## Gỡ lỗi thường gặp

| Vấn đề | Cách xử lý |
|---|---|
| Cổng 8000 đã bị chiếm | Đổi cổng: `uvicorn app.main:app --port 8001` |
| Cổng 5173 đã bị chiếm | Vite tự chọn cổng khác; xem log |
| `pip install` lỗi | Nâng cấp pip: `pip install --upgrade pip` |
| Frontend không gọi được API | Kiểm tra backend đang chạy; mặc định frontend gọi `http://localhost:8000` |