# Thông tin thư viện & giấy phép (THIRD PARTY NOTICES)

Dự án **AI Teaching Assistant** phát hành theo giấy phép [MIT](LICENSE).

Dự án sử dụng các thư viện mã nguồn mở sau. Toàn bộ đều có giấy phép cho phép
sử dụng trong dự án MIT. Bảng này được cập nhật mỗi khi thay đổi dependency.

## Backend (Python)

| Thư viện | Mục đích | Giấy phép |
|---|---|---|
| FastAPI | Framework API | MIT |
| Pydantic | Validation dữ liệu | MIT |
| SymPy | Toán ký hiệu (nguồn sự thật toán học) | BSD-3-Clause |
| Uvicorn | ASGI server | BSD-3-Clause |
| pytest | Kiểm thử | MIT |
| httpx | Test client cho API | BSD-3-Clause |
| Pillow | Xử lý ảnh cho Recognition (kế hoạch) | MIT-CMU (HPND) |

## Frontend (JavaScript/TypeScript)

| Thư viện | Mục đích | Giấy phép |
|---|---|---|
| React | Giao diện | MIT |
| TypeScript | Ngôn ngữ | Apache-2.0 |
| Vite | Build tool | MIT |
| Zustand | Quản lý trạng thái | MIT |
| react-konva / konva | Vẽ canvas cho Whiteboard | MIT |
| JSXGraph | Đồ thị toán học tương tác | LGPL-3.0 + MIT (dual) |
| KaTeX | Hiển thị LaTeX | MIT |
| Plotly.js *(đánh giá)* | Đồ thị thay thế | MIT |
| Vitest | Kiểm thử | MIT |
| React Testing Library | Kiểm thử giao diện | MIT |
| Playwright | Kiểm thử E2E | Apache-2.0 |

## AI / Recognition (kế hoạch tích hợp)

| Thư viện | Mục đích | Giấy phép |
|---|---|---|
| Ollama | Chạy model LLM local | MIT |
| LLaVA / Qwen-VL | Vision model nhận dạng vùng ảnh | Apache-2.0 / Qwen License |
| Pix2Text (P2T) | OCR công thức toán -> LaTeX | Apache-2.0 |

> Lưu ý: Qwen-VL sử dụng giấy phép riêng của Qwen (Apache-2.0 cho model base,
> một số phiên bản có điều khoản sử dụng riêng). Kiểm tra giấy phép trước khi
> phân phối model kèm theo dự án. Các model được tải riêng, không đóng gói vào
> mã nguồn dự án.

## Nguyên tắc

- **Chỉ thêm dependency mã nguồn mở** với giấy phép tương thích MIT
  (MIT, Apache-2.0, BSD, LGPL).
- Khi thêm thư viện mới: cập nhật bảng này trong cùng commit.
- Giữ nguyên thông báo bản quyền gốc của từng thư viện khi phân phối.