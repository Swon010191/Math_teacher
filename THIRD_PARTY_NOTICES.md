# Thông tin thư viện & giấy phép (THIRD PARTY NOTICES)

Dự án **AI Teaching Assistant** phát hành theo giấy phép [MIT](LICENSE).

Dự án sử dụng các thư viện mã nguồn mở sau. Bảng runtime được cập nhật mỗi khi
thay đổi dependency. Công cụ chỉ dùng ở build-time được tách riêng bên dưới và
không thay đổi giấy phép MIT của source code dự án.

## Backend (Python)

| Thư viện | Phiên bản | Mục đích | Giấy phép |
|---|---|---|---|
| FastAPI | 0.115+ | Framework API | MIT |
| Pydantic | 2.x | Validation dữ liệu | MIT |
| SymPy | 1.12+ | Toán ký hiệu (nguồn sự thật toán học) | BSD-3-Clause |
| Uvicorn | 0.30+ | ASGI server | BSD-3-Clause |
| python-dotenv | 1.x | Đọc cấu hình `.env` | BSD-3-Clause |
| python-multipart | 0.x | Multipart upload cho Recognition API | Apache-2.0 |
| pytest | 8.x | Kiểm thử | MIT |
| httpx | 0.27+ | Test client cho API | BSD-3-Clause |

## Frontend (JavaScript/TypeScript)

| Thư viện | Phiên bản | Mục đích | Giấy phép |
|---|---|---|---|
| React | 18.x | Giao diện | MIT |
| TypeScript | 5.x | Ngôn ngữ | Apache-2.0 |
| Vite | 6.x | Build tool | MIT |
| Zustand | 4.x | Quản lý trạng thái | MIT |
| react-konva / konva | 18.x / 9.x | Vẽ canvas cho Whiteboard | MIT |
| JSXGraph | 1.13.x | Đồ thị toán học tương tác | MIT OR LGPL-3.0-or-later |
| KaTeX | 0.16.x | Hiển thị LaTeX | MIT |
| idb-keyval | 6.x | Lưu trữ IndexedDB | Apache-2.0 |
| Vitest | 2.x | Kiểm thử | MIT |
| React Testing Library | 16.x | Kiểm thử giao diện | MIT |
| jsdom | 25.x | Môi trường test | MIT |

> Lưu ý: file `frontend/src/vendor/jsxgraph.css` được copy từ package JSXGraph
> (giấy phép MIT OR LGPL-3.0-or-later) để chạy local, không phụ thuộc CDN.

## Công cụ đóng gói (build-time/runtime launcher)

Các gói dưới đây được dùng khi tạo bản Windows Setup/portable. Chúng không phải
dependency bắt buộc của luồng development nếu chỉ chạy backend và frontend riêng.

| Công cụ | Phiên bản | Mục đích | Giấy phép |
|---|---|---|---|
| PyInstaller | 6.x | Đóng gói backend/launcher | GPL-2.0-or-later + bootloader exception |
| pystray | 0.19.x | Tray icon cho launcher | LGPL-3.0 |
| Pillow | 12.x | Tạo icon tray | HPND/Pillow License |
| uv | 0.12.15 | Tạo runtime Pix2Text khi cài | MIT OR Apache-2.0 |
| Inno Setup | 6.x | Biên dịch installer (chỉ build host) | Inno Setup License |

PyInstaller được sử dụng theo bootloader exception cho phép phân phối chương
trình đã đóng gói. Dự án không sửa source của dependency nào. Bản phát hành
không đóng gói model Ollama/Pix2Text; model được tải riêng và phải tuân theo
điều khoản của nhà cung cấp.

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
  (MIT, Apache-2.0, BSD, LGPL hoặc giấy phép có điều khoản tương thích được
  ghi rõ ở trên).
- Khi thêm thư viện mới: cập nhật bảng này trong cùng commit.
- Giữ nguyên thông báo bản quyền gốc của từng thư viện khi phân phối.
- Phiên bản Python đã khóa trong `backend/requirements.lock`; npm đã khóa trong
  `frontend/package-lock.json`. Dependency chuyển tiếp phải được kiểm tra lại
  khi tạo lock mới.
