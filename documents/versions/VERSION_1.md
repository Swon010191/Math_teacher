# Version 1 - Ban luc moi clone

## Thong tin phien ban

- Baseline: commit `90a3823`.
- Ten commit: `fix(recognition): chuyen LaTeX OCR thanh bieu thuc doc duoc + render KaTeX trong modal xac nhan`.
- Trang thai: da commit tren nhanh `main`.
- Pham vi: toan bo project tai thoi diem bat dau dot cai tien Version 2.

## Tong quan

Version 1 la mot MVP mo rong cua nen tang ho tro giao vien day toan. He thong
chay local, gom bang trang tuong tac, Math Engine dung SymPy, nhan dang cong
thuc va Teacher Copilot. Giao vien van la nguoi xac nhan cong thuc va duyet noi
dung truoc khi dua len bang.

## Chuc nang chinh

### AI Whiteboard

- Ve net tu do, chen text, chon, di chuyen va xoa doi tuong.
- Chon hoac xoa nhieu doi tuong bang cach khoanh vung.
- Zoom, pan bang cong cu Di chuyen hoac chuot giua.
- Keo va thay doi kich thuoc activity tren bang.
- Luu/mo bang bang IndexedDB.
- Xuat va nhap toan bo bang bang JSON.

### Math Engine

Backend FastAPI va SymPy phan tich va tao activity cho 6 nhom ham:

1. Ham bac nhat.
2. Ham bac hai.
3. Ham phan thuc bac nhat tren bac nhat.
4. Ham luong giac `sin` va `cos`.
5. Ham mu.
6. Ham logarit.

Ket qua phan tich bao gom cac dac trung phu hop voi tung loai, nhu nghiem,
dinh, giao diem, tiem can, bien do, chu ky, duong trung binh va tap xac dinh.

### Interactive Teaching Activity

- Do thi JSXGraph tuong tac.
- Cong thuc duoc hien thi bang KaTeX.
- Slider thay doi he so.
- Nut hien/an nghiem, dinh, truc, tiem can hoac cuc tri.
- Chuoi buoc giang day de giao vien tiet lo kien thuc theo tung buoc.
- `ActivityCanvas` va activity registry duoc dung chung cho cac loai ham.

### Recognition

Co ba provider:

- Mock de demo ma khong can cai AI.
- Ollama Vision de nhan dang bang model thi giac local.
- Pix2Text de nhan dang cong thuc toan.

Giao dien cho phep doi provider khi dang chay, xem trang thai kha dung va thu
lai ket noi. Ket qua OCR duoc chuan hoa tu LaTeX sang bieu thuc Math Engine co
the doc, render bang KaTeX va cho phep giao vien sua truoc khi xac nhan.

### Teacher Copilot

- Tao tom tat, kien thuc trong tam, cau hoi goi mo, vi du va cac buoc giang day.
- Co provider `rule_based` khong can AI va provider Ollama chay local.
- Cho phep doi provider tren giao dien.
- Giao vien phai bam dua noi dung len bang sau khi xem va duyet.

## Ky phap dau vao

Version 1 nhan cac cach viet thong dung nhu:

- `4x`, `x^2`, `x**2`, `x²`.
- `sin(x)`, `cos(x)`, `2^x`, `log(x,10)`, `lg(x)`, `log2(x)`.
- Cac ky hieu `·`, `×`, `÷`.
- LaTeX nhu `\frac{2x+3}{x-1}`, `x^{2}`, `\sqrt{x}` va `\pi`.

## Chat luong va van hanh

- Backend, frontend va E2E co bo kiem thu rieng.
- GitHub Actions chay pytest, Vitest, frontend build va Playwright.
- Push tag `v*` co workflow tao GitHub Release.
- README tai baseline ghi nhan 123 backend tests, 62 frontend tests va 13 E2E
  tests.
- Recognition va Copilot co timeout de tranh giao dien cho vo han khi model
  local phan hoi cham.

## Han che cua Version 1

Nhung diem sau la ly do can co Version 2:

- Parser SymPy chua co trust boundary va complexity budget du chat.
- Mot so bieu thuc lon hoac co cau truc dac biet co the gay tinh toan ton kem.
- Ket qua dan xuat chua duoc chan dong bo khi la `NaN` hoac vo cuc.
- Chieu bien thien cua mot so ham mu/log co he so am co the sai.
- Nghiem luong giac tiep xuc, tan so cao hoac phase lon co the bi bo sot hay
  gop sai.
- Phan thuc sau rut gon co the lam mat diem khuyet cua mien xac dinh.
- Copilot co the tin activity type va facts do client gui len.
- Frontend co the thay tham so suy bien bang epsilon, tao do thi hoac facts
  khong dung voi gia tri nguoi dung dang thay.
