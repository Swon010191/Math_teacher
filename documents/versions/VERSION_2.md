# Version 2 - Trustworthy Math Foundation

## Thong tin phien ban

- Baseline: Version 1 tai commit `90a3823`.
- Trang thai: dang phat trien trong working tree, chua commit.
- Ngay ghi nhan: 2026-08-21.
- Muc tieu: tang do an toan cua parser, do dung toan hoc va do tin cay cua
  du lieu Copilot ma khong thay doi y tuong san pham.

## Tong quan thay doi

Version 2 khong tap trung them mot loai activity moi. Dot cai tien nay lam cho
nhung tinh nang da co o Version 1 an toan va dang tin cay hon, dac biet khi dau
vao den tu OCR, nguoi dung hoac client khong duoc tin cay.

Nguyen tac chinh cua Version 2:

- SymPy van la nguon su that toan hoc.
- Moi bieu thuc deu di qua mot parser gioi han.
- Moi facts Copilot deu duoc backend tinh lai tu expression.
- Backend va frontend phai dung cung quy tac toan hoc.
- Trang thai khong hop le phai duoc bao ro, khong tao gia tri thay the gia.

## 1. Parser an toan hon

`backend/app/services/math_service.py` duoc mo rong voi cac lop bao ve:

- Allowlist bien, ham va ten duoc phep.
- Global namespace khong cho truy cap Python builtins.
- Chan underscore, chuoi, attribute va token la.
- Gioi han do dai input, so token va do lon cay bieu thuc.
- Gioi han so mu va bac da thuc du kien.
- Uoc luong operation/node budget truoc cac phep khai trien SymPy.
- Tu choi bieu thuc phi da thuc co nguy co bung no to hop.

Ket qua la payload nguy hiem hoac bieu thuc qua phuc tap duoc tra loi an toan
bang loi 400 thay vi duoc parse hoac tinh toan khong kiem soat.

## 2. Chan ket qua khong huu han

Version 2 them finite gate cho du lieu tinh toan:

- Chan `NaN`, duong vo cuc va am vo cuc.
- Kiem tra truoc va sau cac phep chia, clamp hoac chuyen sang `float`.
- Khong de gia tri khong huu han di vao Pydantic response va bi serialize thanh
  `null`.
- Overflow hoac underflow lam mat y nghia se duoc tra ve nhu mot loi Math Engine
  ro rang.

## 3. Sua do dung ham mu va logarit

- Chieu bien thien tinh theo ca he so ben ngoai va co so.
- Ho tro dung cac dang tuong duong nhu `2**(-x)`, `1/2**x` va `2**(2*x)` khi
  co so hieu dung hop le.
- Khong ket luan ham dong bien chi dua vao co so trong noi dung Copilot.
- Cac co so `<= 0`, bang `1` hoac gia tri khong huu han bi coi la khong hop le.

## 4. Sua nghiem va dac trung luong giac

- Tim nghiem va cuc tri bang cong thuc giai tich thay vi phu thuoc vao sampling
  threshold.
- Tim duoc nghiem tiep xuc nhu truong hop `sin(x) + 1`.
- Xu ly tan so cao ma khong gop nham cac nghiem gan nhau.
- Tolerance dua tren ULP va chu ky, khong dung mot nguong tuyet doi qua lon.
- Gioi han phase va chu ky khong the bieu dien on dinh.
- Sampling dung so buoc co dinh, khong dung vong lap cong float khong gioi han.

## 5. Bao toan mien xac dinh ham phan thuc

- Giu cau truc tu va mau goc truoc khi rut gon.
- Phan biet diem khuyet voi tiem can dung.
- Giu domain exclusions ngay ca khi bieu thuc rut gon thanh da thuc hoac hang.
- Them metadata `holes` vao facts toan hoc va activity.
- Tu choi mau dong nhat bang 0.
- Tu choi rational term vuot bac ho tro, ke ca khi cac term bac cao triet tieu
  sau khi cong.
- Frontend ve diem khuyet bang du lieu backend da xac minh thay vi suy doan bang
  epsilon.

## 6. Tang trust boundary cua Copilot

O Version 1, request Copilot co the mang theo facts do client cung cap. Version
2 thay doi luong nay:

1. Backend nhan expression.
2. Math Engine phan tich lai expression.
3. Backend tu xac dinh activity type.
4. Backend tu tao facts da xac minh.
5. Provider Copilot chi nhan context do backend tao.

Roots, direction, asymptotes hay activity type gia tu client khong con duoc tin
dung. Expression khong hop le duoc API Copilot tra ve loi 400 an toan.

## 7. Frontend khong tao gia tri gia

Version 1 co the thay tham so suy bien bang mot epsilon nho de tiep tuc ve do
thi. Version 2 loai bo hanh vi nay:

- Giu nguyen gia tri nguoi dung dang chon.
- Khong am tham doi `0`, co so `1` hoac mau so suy bien.
- `ActivityCanvas` an graph va facts khi tham so khong hop le.
- Hien thong bao loi de giao vien biet vi sao activity chua the ve.
- Khi slider quay lai mien hop le, activity duoc dung lai voi facts dung.

## 8. Cac file thay doi chinh

Backend:

- `backend/app/services/math_service.py`
- `backend/app/services/activity_service.py`
- `backend/app/services/copilot_service.py`
- `backend/app/providers/rule_based_copilot.py`
- `backend/app/api/copilot.py`
- `backend/app/schemas/math.py`
- `backend/app/schemas/activity.py`
- `backend/app/schemas/copilot.py`

Frontend:

- `frontend/src/features/activities/ActivityCanvas.tsx`
- `frontend/src/features/activities/ExponentialActivity.tsx`
- `frontend/src/features/activities/LogarithmicActivity.tsx`
- `frontend/src/features/activities/RationalActivity.tsx`
- `frontend/src/features/activities/TrigActivity.tsx`
- `frontend/src/features/activities/expMath.ts`
- `frontend/src/features/activities/logMath.ts`
- `frontend/src/features/activities/rationalMath.ts`
- `frontend/src/features/activities/trigMath.ts`

Kiem thu hoi quy duoc bo sung trong `backend/tests/` va `frontend/tests/` cho
parser security, complexity guard, finite values, Copilot facts, rational holes,
trig roots va trang thai activity khong hop le.

## 9. Bang chung kiem thu

Theo ket qua da ghi trong
`documents/implementation/spec-trustworthy-math-foundation.md`:

- Backend complete: 186 tests passed, 1 warning.
- Frontend complete: 80 tests passed.
- Frontend TypeScript va Vite build thanh cong.
- `git diff --check` thanh cong.
- Review gate khong con finding Critical hoac High.

Day la ket qua da duoc ghi nhan trong qua trinh trien khai Version 2, khong phai
ket qua cua mot lan chay test moi khi tao tai lieu phien ban nay.

## 10. Khac biet lon so voi Version 1

Version 1 chung minh project co the hoat dong end-to-end. Version 2 tap trung
chung minh ket qua hien thi co trust boundary ro rang:

- Input khong tin cay bi gioi han.
- Math facts duoc backend xac minh.
- Copilot khong duoc tu tinh hoac tin facts client.
- Domain va cac truong hop bien khong bi mat khi rut gon bieu thuc.
- UI khong che giấu trang thai suy bien bang gia tri thay the.

## Han che con lai

- Version 2 van dang o working tree va chua phai ban phat hanh chinh thuc.
- Chua them cac nhom toan moi nhu `tan`, dao ham, hinh hoc hay ham tong quat.
- Recognition thuc van phu thuoc vao Ollama/Pix2Text local.
- E2E chua chay provider AI thuc trong CI.
- Redesign va responsive layout chua nam trong dot cai tien nay.
- Slider khoi tao ngoai min/max cau hinh van can mot dot xu ly UX rieng.

## 11. AI quet duoc noi dung Text

Vung nhan dang tren bang khong con chi rasterize net but. Version 2 dua ca hai
loai doi tuong sau vao anh OCR theo dung thu tu tren bang:

- Net ve `stroke`.
- Noi dung tao bang cong cu Text.

Anh tam co nen trang de provider OCR xu ly on dinh hon. Vung chi co activity
hoac khong co noi dung co the nhan dang se duoc bo qua an toan. Unit test moi
kiem tra Text-only, thu tu Text/net ve, toa do, thuoc tinh render va cleanup
Konva stage.

## 12. Ho tro ten bien da dang

Math Engine khong con bat buoc bien nguon phai la `x`:

- Nhan cac ten bien ASCII an toan nhu `t`, `u`, `z`, `alpha`.
- Nhan dinh nghia ham nhu `z = 2*t + 1` va `f(t) = t^2 - 1`.
- Loi tinh toan van chay tren symbol noi bo duoc kiem soat; API bao toan ten
  bien nguon va bien phu thuoc de hien thi.
- Activity, cong thuc KaTeX, nghiem, mien xac dinh, tiem can va Copilot dung ten
  bien goc thay vi doi ve `x/y`.
- Activity cu khong co metadata van mac dinh `x/y`.

Parser tiep tuc dung allowlist, namespace gioi han, complexity budget va finite
gate. Ten bien dong khong duoc phep mo rong quyen truy cap Python object.

## 13. Giai phuong trinh bac nhat va bac hai

Backend co endpoint `POST /api/math/solve` voi dau vao:

```json
{
  "expression": "x + y = 2",
  "solve_for": "x"
}
```

Solver:

- Giai phuong trinh bac nhat va bac hai tren mien thuc.
- Giu nghiem chinh xac va them gia tri gan dung khi co the.
- Ho tro chon an can giai; cac symbol con lai duoc xem la tham so.
- Phan biet da giai, vo nghiem, vo so nghiem va ket qua phu thuoc dieu kien.
- Tra cac buoc deterministic gom bieu thuc, LaTeX va giai thich.
- The nghiem lai vao phuong trinh de danh dau `verified`.
- Tu choi bac lon hon 2, payload nguy hiem va bieu thuc vuot budget.

Vi du da duoc bao ve bang test:

- `2u + 3 = 9` cho `u = 3`.
- `t^2 - 1 = 0` cho `t = -1` va `t = 1`.
- `u^2 - 2 = 0` giu dang `+-sqrt(2)`.
- `x + y = 2`, giai theo `x`, cho `x = 2 - y`.

## 14. Tu dong phan loai va activity loi giai

Modal xac nhan dung chung cho OCR va nhap ban phim tu phan loai:

- `z = 2t + 1`: phan tich ham so.
- `2u + 3 = 9`: giai phuong trinh.
- `x + y = 2`: giai phuong trinh va bat buoc chon an.
- `t^2 - 1`: tao activity do thi va dinh kem nghiem cua `t^2 - 1 = 0`.

Phuong trinh tao activity `equation_solution` rieng. Ham bac nhat va bac hai
van giu do thi, slider va cac dac trung cu, dong thoi co muc thu gon
"Dap an & loi giai". Dap an va cac buoc den tu backend/SymPy, khong do LLM tu
tinh. Copilot chi tiep tuc phuc vu activity ham so.

Recognition providers bao toan ve trai va dau `=` thay vi bo `y=` qua som.
Activity luu lai confidence va cong thuc OCR da duoc giao vien xac nhan.

## 15. Bang chung kiem thu sau dot mo rong

Ket qua chay lai sau khi them quet Text, bien dong, solver va activity loi giai:

- Backend complete: 227 tests passed, 1 warning.
- Frontend complete: 101 tests passed.
- Frontend TypeScript va Vite build thanh cong.
- Playwright nhan du 18 kich ban E2E, trong do co Text-only, phuong trinh mot
  bien, chon an cho phuong trinh nhieu bien va ham `z=f(t)`.
- E2E chua chay tren may hien tai vi chua cai Chromium binary cua Playwright.

Canh bao build con lai la canh bao da biet cua JSXGraph ve `eval` noi bo va
bundle lon; khong phai loi moi cua solver.

## 16. Frontend Blueprint va activity khong xung dot

Activity khong con xep do thi, loi giai va Copilot noi tiep trong mot khung co
chieu cao co dinh. Moi card co cac tab `Do thi`, `Loi giai`, `Goi y` va mot vung
noi dung cuon duy nhat. Chi tab dang chon duoc render, nen controls cua do thi
khong the ve de len loi giai hoac Copilot.

Dot cai tien giao dien con bao gom:

- Nen bang dang giay luoi toan hoc nhe, mau cobalt va card nhu phieu bai giang.
- JSXGraph resize theo card bang `ResizeObserver`.
- Konva Stage resize theo board container.
- Zoom card dong nhat voi net ve; co nut thu nho, phong to va reset.
- Activity moi duoc dat lech nhau va card dang chon nam tren cung.
- Toolbar doi ten ro nghia: `Van ban`, `Nhan dang`, `Tay vung`.
- Pointer events cho chuot, but va touch; vung Nhan dang dung mau tim thay vi
  mau do destructive.
- Mobile co focus mode va nut thu nho activity; modal dung dang bottom sheet.
- Modal cho phep override Ham so/Phuong trinh, hien dien giai chuan hoa va loi
  API inline.
- Xoa activity object dong thoi don record activity khoi du lieu luu/export.

## 17. Ham viet dao hai ve

Frontend va backend cung ap dung quy tac doi xung:

- `y=2x+1` va `2x+1=y` deu la ham co bien nguon `x`, bien phu thuoc `y`.
- Input dao duoc chuan hoa ve `y=2x+1` truoc khi tao activity.
- `f(t)=2t+1` va `2t+1=f(t)` cung duoc backend hieu tuong duong.
- `x+y=2`, `2x+1=5`, `x=2` van la phuong trinh, khong bi phan loai nham.

Regression tests bao ve classifier, API analyze/activity, metadata bien, tab
activity, resize graph va request canonical gui tu frontend.

## 18. Sua JSXGraph co dan va bien mat

`ResizeObserver` tung goi `resizeContainer(width, height)` trong khi container
dung `border-box` va co border. JSXGraph ghi kich thuoc client vao inline CSS,
lam moi vong observer bi tru tiep kich thuoc cho den khi do thi bien mat.

Version 2 goi `resizeContainer(width, height, true)` de CSS tiep tuc so huu kich
thuoc container. Observer dung target on dinh, bo qua callback sau cleanup va
xoa curve ref khi React StrictMode replay effect. Unit va E2E regression kiem
tra resize, chuyen tab va kich thuoc do thi khong co dan theo thoi gian.

## 19. Loi giai chi tiet theo chuong trinh pho thong

`SolveStep` co them metadata tuy chon de frontend hieu y nghia tung buoc ma van
doc duoc response cu. Math Engine sinh deterministic:

- Bac nhat: dua ve dang chuan, xac dinh he so, co lap hang tu chua an, chia hai
  ve, ket luan va the nghiem.
- Bac hai: xac dinh `a`, `b`, `c`, tinh biet thuc, xet truong hop, ap dung cong
  thuc nghiem, rut gon va the tung nghiem.
- Truong hop suy bien hoac he so tham so khong chia vo dieu kien.

Moi gia tri van do SymPy tinh chinh xac. LLM khong tham gia quyet dinh nghiem.

## 20. Tab Kien thuc va nguon quoc te

Activity bac nhat/bac hai co tab `Kien thuc` rieng. Tab tu tai khi duoc mo lan
dau, hien noi dung Viet tich hop va cac nguon allowlist:

- `vi.wikipedia.org`.
- `en.wikipedia.org`.
- `en.wikibooks.org`.

API `POST /api/knowledge/related` tu parse expression va suy topic; client khong
duoc gui topic hoac URL. Request ra ngoai chi chua ten trang chu de co dinh,
khong chua anh bang, expression hoac du lieu lop hoc. Response co link bai,
contributors, revision, ngay truy xuat va giay phep. Remote text duoc chuyen ve
plain text, gioi han dung luong va khong render bang HTML tho.

Frontend co nut `Tieng Viet / Original`, gan nhan ban dich may, bao khi khong co
ban dich va cache response hop le trong IndexedDB. Backend co bounded memory TTL
cache, stale-if-error va fallback Viet tich hop. Ollama translation la tuy chon,
mac dinh tat.

## 21. Toolbar AI khong can cuon ngang

Toolbar tach thanh action rail co the cuon va nut `AI` co dinh o mep phai. Bang
provider mac dinh an, chi tai diagnostics khi mo; Escape va click ben ngoai dong
bang. Desktop dung popover khong bi ancestor overflow cat, mobile dung panel co
gioi han chieu cao o day man hinh.

## 22. Bang chung kiem thu hien tai

- Backend complete: 245 tests passed, 1 warning co san cua Starlette TestClient.
- Frontend complete: 108 tests passed.
- Frontend TypeScript va Vite production build thanh cong.
- `git diff --check` thanh cong.
- Playwright discovery nhan du 21 kich ban E2E.
- Browser E2E chua chay vi may hien tai thieu Chromium headless shell cua
  Playwright; lenh bao can chay `npx playwright install`.

Canh bao build con lai la canh bao da biet cua JSXGraph ve `eval` noi bo va
bundle lon.
