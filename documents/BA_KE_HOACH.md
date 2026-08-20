# Kế hoạch BA - AI Teaching Assistant (Math Teacher)

| | |
|---|---|
| **Dự án** | AI Teaching Assistant - Nền tảng giảng dạy AI mã nguồn mở |
| **Vai trò tài liệu** | Kế hoạch phân tích nghiệp vụ (BA) |
| **Ngày** | 2026-08-20 |
| **Trạng thái** | Đã được khách hàng duyệt |

## 1. Mục tiêu

Biến nội dung giáo viên viết trên bảng thành **hoạt động giảng dạy tương tác**
(đồ thị, slider, tiết lộ đáp án theo bước) ngay trên một chiếc bảng điện tử,
do giáo viên kiểm soát hoàn toàn. Sản phẩm **không phải chatbot**.

## 2. Các thành phần sản phẩm

| Ký hiệu | Thành phần | Vai trò | Trong MVP Stage 1 |
|---|---|---|---|
| B | AI Whiteboard | Bảng điện tử, sản phẩm chính | Có |
| A | Interactive Teaching Canvas | Widget tương tác trên bảng | Có (chỉ hàm bậc hai) |
| D | Teacher Copilot | AI tạo nội dung sư phạm | Sau (Stage 3) |
| C | Open Teaching Activity | Định dạng mở + hệ sinh thái | Chỉ JSON schema + export/import |

## 3. Quyết định khách hàng (đã chốt)

| Hạng mục | Quyết định |
|---|---|
| Phạm vi Stage 1 | Whiteboard + Recognition + Activity hàm bậc hai + Math Engine + lưu local |
| Luồng nhập chính | **Viết tay là chính** (vẽ -> chọn vùng -> nhận dạng -> xác nhận/sửa); gõ phím là dự phòng |
| Ngôn ngữ giao diện | Tiếng Việt |
| Thư viện đồ thị | JSXGraph |
| Recognition | **Mock trước** -> Ollama + LLaVA/Qwen-VL (Vision) -> Pix2Text (Math OCR) -> Production thật |
| Repository | github.com/Swon010191/Math_teacher (MIT) |
| Giao diện chạy | Trình duyệt desktop |

## 4. Yêu cầu phi chức năng (bắt buộc)

1. **Mã nguồn mở:** mọi dependency phải là open source (MIT/Apache/BSD/LGPL),
   ghi rõ trong `THIRD_PARTY_NOTICES.md`.
2. **Commit:** mọi thay đổi commit lên GitHub với message có nghĩa.
3. **Build từ nguồn:** cài đặt/biên dịch được từ mã nguồn, có hướng dẫn rõ.
4. **Tài liệu:** README, CHANGELOG, bug tracker (GitHub Issues), tài liệu hướng dẫn.
5. **Local-first:** không bắt buộc tài khoản, cloud hay API key.
6. **Chịu lỗi:** khi AI lỗi/tắt, Math Core và Whiteboard vẫn hoạt động.
7. **An toàn dữ liệu:** không gửi nét vẽ/dữ liệu lớp học ra cloud khi chưa đồng ý.

## 5. Nguyên tắc nghiệp vụ cốt lõi

- **Math Engine (SymPy) là nguồn sự thật toán học** (nghiệm, đỉnh, trục đối xứng...).
- LLM chỉ đề xuất nội dung sư phạm; đầu ra là JSON có schema, được validate.
- Giáo viên luôn được **xem và sửa** trước khi nội dung lên bảng.
- Nhận dạng viết tay không đảm bảo 100% chính xác -> bước **xác nhận/sửa là bắt buộc**.

## 6. Phạm vi Stage 1 (MVP)

**Có:**
- Whiteboard tối giản: bút, chọn vùng, text, di chuyển, xóa, zoom/pan
- Lưu local (IndexedDB) + JSON export/import
- Nhập công thức: viết tay (luồng chính, qua Mock Recognition) + gõ phím (dự phòng)
- Màn hình xác nhận/sửa kết quả nhận dạng
- Math Engine: parse + tính đỉnh/nghiệm/trục đối xứng/giao điểm trục + sinh dữ liệu đồ thị
- Activity hàm bậc hai: đồ thị (JSXGraph) + slider a,b,c + hiện/ẩn đỉnh-nghiệm-trục
  + chuỗi bước giảng dạy + kéo/resize trên bảng
- Activity Model JSON có `schemaVersion`

**Chưa có:**
- Tài khoản, cloud storage, realtime collaboration
- Plugin/marketplace, knowledge graph, RAG quy mô lớn
- Teacher Copilot (thuộc giai đoạn sau)
- Recognition thực (Ollama/Pix2Text) - thay Mock sau khi demo ổn định

## 7. Lộ trình triển khai

| Phase | Nội dung | Kết quả |
|---|---|---|
| 0 | Khởi tạo git + documents/ + nền móng mã nguồn mở | Repo sẵn sàng |
| 1 | Backend Math Engine (FastAPI + SymPy + Pydantic + pytest) | API + tests |
| 2 | Frontend Whiteboard (React + Vite + TS + react-konva + Zustand) | Bảng vẽ hoạt động |
| 3 | Recognition: interface + Mock Provider + màn hình xác nhận | Luồng vẽ -> nhận dạng -> xác nhận |
| 4 | Teaching Canvas (JSXGraph) + Activity JSON schema | Activity hàm bậc hai |
| 5 | Đóng gói docs, E2E test, release | Demo hoàn chỉnh |

## 8. Tiêu chí thành công (đối chiếu mục 13 tài liệu gốc)

1. Người dùng viết hoặc nhập được hàm bậc hai.
2. Hệ thống nhận dạng và cho phép xác nhận biểu thức.
3. Math Engine tính đúng các đặc trưng.
4. Activity xuất hiện trực tiếp trên whiteboard.
5. Giáo viên điều chỉnh hệ số bằng slider.
6. Giáo viên kiểm soát việc hiện đáp án.
7. (Stage 3) Local AI tạo được giải thích/câu hỏi.
8. Khi tắt Generative AI, chức năng toán và whiteboard vẫn chạy.
9. Bảng được lưu và mở lại trên máy.
10. Không bắt buộc tài khoản hoặc cloud API trả phí.

## 9. Rủi ro & giả định

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| Nhận dạng viết tay sai | Trung bình | Bước xác nhận/sửa bắt buộc; gõ phím dự phòng |
| Model local cần cấu hình máy khá | Thấp | Mock trước; AI không nằm trên critical path |
| JSXGraph kết hợp React/DOM overlay | Trung bình | Activity là React component trên lớp DOM, theo tài liệu |
| Phạm vi Recognition rộng | Trung bình | Chia giai đoạn: Mock -> Vision -> Math OCR |