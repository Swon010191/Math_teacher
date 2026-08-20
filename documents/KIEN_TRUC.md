# Kiến trúc hệ thống (ARCHITECTURE)

## 1. Tổng quan

```
FRONTEND (React + Vite + TypeScript)
  - AI Whiteboard          (react-konva)
  - Interactive Teaching Canvas (JSXGraph + React + KaTeX)
  - Recognition UI / Math API client / Copilot UI (giai đoạn sau)
  - Zustand stores | IndexedDB | JSON export/import
        |
        | REST (JSON)
        v
BACKEND (FastAPI + Python)
  - /api/math       Math Service        (SymPy - nguồn sự thật toán học)
  - /api/recognize  Recognition Service (RecognitionProvider)
  - /api/copilot    Teacher Copilot     (GenerativeAIProvider - giai đoạn sau)
        |
        v
RecognitionProvider: Mock (Stage 1) -> Ollama Vision (LLaVA/Qwen-VL) -> Pix2Text
```

## 2. Nguyên tắc kiến trúc

1. **Math Engine là nguồn sự thật toán học.** LLM chỉ đề xuất nội dung sư phạm,
   không được dùng để tính nghiệm, đạo hàm hay kết luận đáp án.
2. **Provider thay thế được:** `RecognitionProvider` và `GenerativeAIProvider`
   là interface; thay Mock bằng implementation thật mà không đổi UI.
3. **Local-first:** IndexedDB lưu bảng trên máy; JSON export/import để sao lưu
   và chia sẻ activity; không bắt buộc tài khoản hay cloud.
4. **Không phụ thuộc AI:** Math Core + Whiteboard hoạt động độc lập; khi AI
   lỗi/tắt, mọi chức năng toán học và bảng vẽ vẫn chạy.
5. **Luồng chính:** nét vẽ -> chọn vùng -> Recognition -> xác nhận/sửa ->
   Math Engine -> tạo Activity -> giáo viên duyệt -> hiển thị trên bảng.
6. **Bước xác nhận là bắt buộc:** nhận dạng viết tay không đảm bảo chính xác
   tuyệt đối; giáo viên luôn xem và sửa trước khi phân tích.

## 3. Activity Model (JSON, có schemaVersion)

```json
{
  "schemaVersion": "1.0",
  "type": "quadratic_function",
  "source": { "latex": "y=x^2-4x+3", "confidence": 0.94, "confirmed": true },
  "math": {
    "expression": "x**2-4*x+3",
    "vertex": [2, -1],
    "roots": [1, 3],
    "axis": "x=2"
  },
  "widgets": [
    { "type": "graph" },
    { "type": "parameter_slider", "parameters": ["a", "b", "c"] }
  ],
  "steps": [
    { "visible": ["graph"] },
    { "visible": ["graph", "axis"] },
    { "visible": ["graph", "axis", "vertex", "roots"] }
  ]
}
```

**Quy tắc an toàn:** AI chỉ đề xuất dữ liệu theo schema; không bao giờ thực thi
mã do model sinh ra. Mọi đầu ra AI được validate bằng schema trước khi hiển thị.

## 4. Recognition - lộ trình 4 bước

| Bước | Provider | Mục đích | Khi nào |
|---|---|---|---|
| 1 | MockRecognitionProvider | Hoàn thiện UI + luồng xử lý | Stage 1 (ngay) |
| 2 | OllamaVisionProvider (LLaVA/Qwen-VL) | Hiểu hình ảnh vùng chọn | Sau demo ổn định |
| 3 | Pix2TextProvider | Nhận dạng công thức toán -> LaTeX/cấu trúc | Sau Vision |
| 4 | Production provider | Thay Mock bằng implementation thật | Sau khi demo ổn định |

## 5. Stack kỹ thuật

| Lớp | Công nghệ | Giấy phép |
|---|---|---|
| Frontend | React, TypeScript, Vite, Zustand, react-konva | MIT / Apache-2.0 |
| Đồ thị | JSXGraph | LGPL-3.0 + MIT (dual) |
| Math render | KaTeX | MIT |
| Backend | Python, FastAPI, Pydantic, SymPy, Uvicorn | MIT / BSD-3-Clause |
| Local AI | Ollama | MIT |
| Lưu trữ | IndexedDB, JSON export/import | - |

## 6. Cấu trúc mã nguồn

- `backend/app/api` - REST endpoints (math, recognize)
- `backend/app/domain` - mô hình miền (Activity, biểu thức)
- `backend/app/services` - Math Service, Recognition Service
- `backend/app/providers` - RecognitionProvider (Mock, tương lai: Ollama, Pix2Text)
- `backend/app/schemas` - Pydantic schemas (validation)
- `frontend/src/features/board` - AI Whiteboard
- `frontend/src/features/activities` - Teaching Canvas + Activity Model
- `frontend/src/features/recognition` - UI nhận dạng + xác nhận
- `frontend/src/features/math` - client gọi Math Engine
- `frontend/src/stores` - Zustand stores (board, activity, recognition)