# Hướng dẫn đóng góp

Cảm ơn bạn quan tâm đến dự án **AI Teaching Assistant**! Dự án là phần mềm mã
nguồn mở (giấy phép MIT) và hoan nghênh mọi đóng góp từ cộng đồng.

## Báo cáo lỗi và đề xuất tính năng

Sử dụng **GitHub Issues** làm bug tracker chính thức:

- [Báo cáo lỗi](.github/ISSUE_TEMPLATE/bug_report.md)
- [Đề xuất tính năng](.github/ISSUE_TEMPLATE/feature_request.md)

Trước khi tạo issue, hãy tìm kiếm xem vấn đề đã được báo cáo chưa.

## Quy trình đóng góp

1. **Fork** repository về tài khoản của bạn.
2. **Tạo nhánh** từ `main` với tên có ý nghĩa:
   ```bash
   git checkout -b feat/ten-tinh-nang
   git checkout -b fix/ten-loi
   ```
3. **Phát triển** và đảm bảo:
   - Mã tuân thủ style hiện tại của dự án.
   - Viết test cho chức năng mới / lỗi đã sửa.
   - Tất cả test hiện có vẫn chạy (`pytest` cho backend, `npm test` cho frontend).
4. **Commit** với message có ý nghĩa theo chuẩn Conventional Commits:
   ```
   feat: thêm slider cho hệ số a, b, c
   fix: sửa lỗi parse biểu thức chứa dấu trừ
   docs: bổ sung tài liệu cài đặt
   test: thêm unit test cho Math Engine
   ```
5. **Push** nhánh lên fork và tạo **Pull Request** lên `main`.

## Quy tắc mã nguồn

- **Nguồn sự thật toán học là Math Engine (SymPy).** Không đưa tính toán vào LLM.
- **Mọi đầu ra AI phải là JSON có schema và được validate.**
- **Không bao giờ** đưa nội dung lên bảng khi chưa có sự duyệt của giáo viên.
- **Chỉ sử dụng dependency mã nguồn mở.** Khi thêm thư viện mới, cập nhật cả
  `THIRD_PARTY_NOTICES.md`.
- Không lưu API key hoặc bí mật trong source code hoặc commit.
- Dữ liệu lớp học không được gửi lên cloud khi chưa được đồng ý.

## Chuẩn commit

- Message viết bằng tiếng Việt (hoặc tiếng Anh), ngắn gọn, mô tả **tại sao** và **cái gì**.
- Một commit cho một thay đổi logic; tách riêng commit cho từng mục đích.
- Tham khảo số issue liên quan khi cần: `fix: sửa ... (#12)`.

## Cài đặt môi trường phát triển

Xem [docs/HUONG_DAN_CAI_DAT.md](docs/HUONG_DAN_CAI_DAT.md) và
[README.md](README.md).

## Giấy phép

Bằng việc đóng góp, bạn đồng ý các đóng góp của mình được phát hành theo
giấy phép [MIT](LICENSE) của dự án.