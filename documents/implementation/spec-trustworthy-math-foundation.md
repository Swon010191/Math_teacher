---
title: 'Trustworthy Math Foundation'
type: 'bugfix'
created: '2026-08-21'
status: 'done'
review_loop_iteration: 6
baseline_commit: '90a3823'
context:
  - 'documents/REQUIREMENTS.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Math Engine đang parse input chưa đủ giới hạn; một số đặc trưng hàm mũ, logarit, lượng giác và phân thức có thể sai; frontend âm thầm đổi tham số suy biến; Copilot tin facts do client gửi. Các hành vi này có thể tạo nội dung giảng dạy sai dù test hiện tại vẫn xanh.

**Approach:** Thiết lập một trust boundary thống nhất: mọi biểu thức đi qua parser giới hạn, mọi facts Copilot được backend tính lại, backend/frontend dùng cùng quy tắc toán học, và trạng thái tham số không hợp lệ được báo rõ thay vì thay bằng giá trị giả.

## Boundaries & Constraints

**Always:** Giữ SymPy là nguồn sự thật; giữ tương thích ký pháp đang hỗ trợ như `4x`, `x^2`, LaTeX, `lg`, `log2`; đầu vào không tin cậy phải bị từ chối trước khi truy cập Python object hoặc gọi phép tính không kiểm soát; test phải chứng minh lỗi trước khi sửa.

**Ask First:** Thay đổi public API schema; thêm dependency; loại bỏ một dạng biểu thức từng được công bố hỗ trợ; thay đổi format board/activity đã export.

**Never:** Dùng `eval` hoặc thực thi code sinh bởi AI; dùng LLM để xác nhận kết quả toán; âm thầm thay `0`, cơ số `1`, hoặc mẫu số suy biến bằng epsilon; redesign giao diện trong story này.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|----------------------------|----------------|
| Ký pháp hợp lệ | `4x`, `x^2`, LaTeX, sin/cos/log/exp được hỗ trợ | Parse và phân tích như trước | N/A |
| Payload nguy hiểm | attribute, underscore, string, symbol/hàm lạ | Không được parse hoặc thực thi | API trả 400 với thông báo an toàn |
| Copilot facts giả | Expression đúng nhưng roots/direction do client sửa | Provider nhận facts backend tính lại | Bỏ qua facts client |
| Hàm mũ/log hệ số âm | `-2^x`, `-log(x,2)` | Chiều biến thiên đúng theo cả hệ số và cơ số | N/A |
| Nghiệm lượng giác tiếp xúc | `sin(x)+1` | Tìm được nghiệm tiếp xúc trong cửa sổ phân tích | N/A |
| Phân thức có điểm khuyết | Biểu thức có nhân tử bị triệt tiêu | Không làm mất hạn chế miền xác định | N/A |
| Slider suy biến | `a=0`, `b=0`, base `=1`, mẫu đồng nhất bằng 0 | Giữ nguyên giá trị, không dựng facts giả | Hiện trạng thái không hợp lệ |

</frozen-after-approval>

## Code Map

- `backend/app/services/math_service.py` -- parse và tính đặc trưng toán học.
- `backend/app/services/copilot_service.py` -- tạo context cho provider Copilot.
- `backend/app/providers/rule_based_copilot.py` -- diễn giải sư phạm phải bám facts đã xác minh.
- `backend/app/api/copilot.py` -- ánh xạ lỗi biểu thức thành HTTP 400.
- `backend/tests/test_math_service.py` -- regression và parser security tests.
- `backend/tests/test_api.py` -- kiểm tra trust boundary qua API.
- `frontend/src/features/activities/{expMath,logMath,trigMath,rationalMath}.ts` -- tính toán hiển thị tức thời.
- `frontend/src/features/activities/ActivityCanvas.tsx` -- báo trạng thái tham số không hợp lệ.
- `frontend/tests/{expMath,logMath,trigMath,rationalMath}.test.ts` -- regression phía client.

## Tasks & Acceptance

**Execution:**
- [x] `backend/tests/test_math_service.py` -- thêm test đỏ cho payload nguy hiểm và các lỗi toán đã xác định.
- [x] `backend/app/services/math_service.py` -- thêm parser allowlist/complexity guard; sửa mũ, log, lượng giác và domain phân thức.
- [x] `backend/tests/test_api.py` -- thêm test Copilot với facts giả và expression không hợp lệ.
- [x] `backend/app/services/copilot_service.py`, `backend/app/api/copilot.py` -- tính lại context từ expression và trả lỗi 400 an toàn.
- [x] `frontend/tests/*Math.test.ts` -- thay assertion đang hợp thức hóa epsilon bằng assertion trạng thái invalid và kết quả đúng.
- [x] `frontend/src/features/activities/*Math.ts`, `ActivityCanvas.tsx` -- loại bỏ silent substitution, sửa feature calculations và hiển thị lỗi tham số.
- [x] `backend/app/services/math_service.py` -- chặn số không hữu hạn/số mũ lồng trước expand, giữ phân loại `exp(-x)`, giới hạn chu kỳ và nghiệm log cực trị.
- [x] `backend/app/services/math_service.py`, `backend/app/services/activity_service.py` -- bảo toàn hệ số gốc và metadata điểm khuyết của phân thức bậc nhất/bậc nhất; từ chối biểu thức bậc cao dù triệt tiêu.
- [x] `backend/app/services/copilot_service.py`, `backend/app/providers/rule_based_copilot.py` -- dùng biểu thức đọc được, direction đã xác minh và phân biệt điểm khuyết với tiệm cận.
- [x] `frontend/src/features/activities/trigMath.ts`, `frontend/src/features/activities/rationalMath.ts` -- tính cực trị/nghiệm lượng giác giải tích và không suy đoán triệt tiêu bằng epsilon.
- [x] `backend/tests/`, `frontend/tests/` -- thêm regression cho mọi finding vòng review 1 và component invalid → valid.
- [x] `backend/app/services/math_service.py` -- lấy mẫu theo số bước hữu hạn; giới hạn phase/period; không làm tròn/gộp nghiệm trig theo ngưỡng tuyệt đối; tránh float underflow.
- [x] `backend/app/services/math_service.py` -- phân loại an toàn phân thức hằng có điểm khuyết, tổng phân thức và các dạng mũ nghịch đảo/lũy thừa tuyến tính được hỗ trợ.
- [x] `backend/app/providers/rule_based_copilot.py` -- loại bỏ mọi câu suy diễn direction chỉ từ cơ số; toàn bộ prose phải bám `m.direction`.
- [x] `frontend/src/features/activities/trigMath.ts`, `frontend/src/features/activities/rationalMath.ts`, `frontend/src/features/activities/RationalActivity.tsx` -- dedup theo sai số tương đối, xử lý decimal cancellation ổn định và vẽ điểm khuyết.
- [x] `backend/tests/`, `frontend/tests/` -- regression cho mọi finding vòng review 2, gồm tần số/phase cực trị, rational constant holes và decimal coefficients.
- [x] `backend/app/services/math_service.py`, `frontend/src/features/activities/trigMath.ts` -- dùng tolerance theo ULP/chu kỳ, không có sàn tuyệt đối làm gộp hoặc nhận nghiệm ngoài cửa sổ.
- [x] `backend/app/services/math_service.py` -- chặn projected polynomial degree trước expand và dedup domain exclusions ở dạng SymPy chính xác.
- [x] `frontend/src/features/activities/RationalActivity.tsx` -- ưu tiên verified `activity.math.holes` cho trạng thái ban đầu và tính đúng tọa độ hole của tổng phân thức.
- [x] `backend/app/providers/rule_based_copilot.py` -- không mô tả `a/c` khi mẫu hệ số hằng bằng 0; chỉ dùng asymptote facts có thật.
- [x] `backend/tests/`, `frontend/tests/` -- regression cho mọi finding vòng review 3.
- [x] `backend/app/services/math_service.py` -- phân loại cấu trúc có denominator trước wildcard match để chặn DoS và giữ exclusions dù biểu thức rút gọn thành polynomial.
- [x] `backend/app/services/math_service.py`, `frontend/src/features/activities/trigMath.ts` -- clamp target gần `±1`, dedup nghiệm tiếp xúc và từ chối phase/period dưới độ phân giải ULP.
- [x] `frontend/src/features/activities/rationalMath.ts` -- so proportional coefficients sau normalization, không nhân trực tiếp gây underflow.
- [x] `backend/tests/`, `frontend/tests/` -- regression có timeout cho rational cancellation DoS, polynomial-with-hole, tangent roots và tiny coefficients.
- [x] `backend/app/services/math_service.py` -- kiểm tra bậc từng rational term trước khi cộng/triệt tiêu và từ chối denominator đồng nhất bằng 0.
- [x] `frontend/src/features/activities/RationalActivity.tsx` -- dùng verified initial holes/asymptotes không suy đoán gần bằng; tọa độ hole lấy giới hạn đúng thay vì fallback 0.
- [x] `backend/tests/`, `frontend/tests/` -- regression cho cubic term cancellation, zero-over-zero và verified near-equal/hole-y activities.
- [x] `backend/app/services/math_service.py` -- chặn combinatorial expansion của biểu thức phi đa thức trước `sp.expand` bằng operation/node budget.
- [x] `backend/app/services/math_service.py` -- kiểm tra hữu hạn trước tolerance/clamp nghiệm trig và sau mọi derived fact trước tạo schema response.
- [x] `backend/tests/` -- regression timeout cho tích trig và HTTP 400 cho ratio/derived-fact overflow.

**Acceptance Criteria:**
- Given payload không nằm trong allowlist, when gọi math hoặc Copilot API, then request trả 400 và không thực thi hành vi Python ngoài miền toán được hỗ trợ.
- Given ký pháp hợp lệ hiện tại, when phân tích, then kết quả tương thích với hành vi đã công bố.
- Given client gửi facts hoặc activity type giả, when gọi Copilot, then provider chỉ nhận dữ kiện được backend tính lại từ expression.
- Given hệ số âm, nghiệm tiếp xúc hoặc điểm khuyết phân thức, when phân tích, then backend và frontend trả đặc trưng toán học đúng.
- Given slider ở trạng thái suy biến, when render activity, then giá trị nhập không bị thay đổi và UI không hiển thị facts giả.
- Given toàn bộ thay đổi, when chạy test và build, then backend, frontend và TypeScript build đều đạt.

## Spec Change Log

- Review loop 1: review phát hiện guard số chưa chặn scientific infinity/nested exponent; rational activity làm mất điểm khuyết; Copilot vẫn diễn giải sai direction/điểm khuyết và dùng `srepr`; nghiệm/cực trị trig frontend còn phụ thuộc sampling. Tasks và Design Notes được mở rộng để chặn các known-bad states này. KEEP: public API tương thích, parser allowlist, facts Copilot tính lại phía server, giá trị slider không bị thay bằng epsilon, lỗi invalid hiển thị rõ.
- Review loop 2: review phát hiện chu kỳ/phase lượng giác hữu hạn nhưng cực lớn có thể treo sampling; nghiệm tần số cao bị gộp; rational hằng có hole gây 500; decimal cancellation lệch frontend; prose Copilot còn câu suy diễn sai direction. Tasks được mở rộng để dùng vòng lấy mẫu hữu hạn, tolerance theo scale/period, phân loại rational từ cấu trúc gốc và kiểm thử prose hoàn chỉnh. KEEP toàn bộ review loop 1; giữ analytical trig, holes metadata, human-readable expression và component invalid → valid.
- Review loop 3: review không còn Critical nhưng còn High ở tolerance trig cực nhỏ và RationalActivity bỏ qua verified holes của tổng phân thức; đồng thời projected degree và Copilot rational hằng cần guard. Tasks được siết theo ULP/symbolic identity và verified metadata. KEEP toàn bộ hai vòng trước, đặc biệt fixed-count sampling, exponential-equivalent support, API compatibility và server-derived Copilot facts.
- Review loop 4: closure review tái hiện DoS khi wildcard trig match chạy trên rational cancellation, mất hole khi tổng rational rút gọn thành polynomial, tangent target trôi quanh ±1, phase lớn hơn độ phân giải chu kỳ và underflow cross-product frontend. Tasks được bổ sung structural routing trước wildcard match, representability guard và normalized coefficient comparison. KEEP toàn bộ vòng 1-3 cùng regression hiện có.
- Review loop 5: final gate phát hiện cubic rational term trong tổng vẫn vượt degree guard sau triệt tiêu, denominator đồng nhất zero bị nhận như rational hợp lệ, và RationalActivity suy diễn verified holes sai cho hệ số gần bằng/tọa độ hole. Tasks được bổ sung per-term structural degree checks, zero-denominator rejection và verified initial feature rendering. KEEP toàn bộ vòng 1-4 và public API compatibility.
- Review loop 6 (human-approved override): terminal gate sau giới hạn workflow phát hiện combinatorial `sp.expand` DoS với tích trig, ratio trig overflow bị clamp thành nghiệm giả và derived facts không hữu hạn serialize thành null. Người dùng cho phép đúng một vòng sửa cuối. Tasks bổ sung pre-expand operation budget và finite validation xuyên suốt. KEEP toàn bộ vòng 1-5.

## Design Notes

Parser phải dùng local/global dictionary giới hạn và hậu kiểm free symbols; token chứa underscore, dấu nháy hoặc dấu chấm bị từ chối trước parse. Guard phải kiểm tra hữu hạn sau mọi phép đổi `float`, giới hạn số mũ khoa học và đánh giá đệ quy exponent trước `expand`. Phân loại phải nhận diện hàm mũ trước rational representation.

Phân thức dùng tử/mẫu gốc để kiểm tra bậc, hệ số và domain exclusions; biểu thức rút gọn chỉ phục vụ giới hạn/tiệm cận. Điểm khuyết là metadata riêng, không phải tiệm cận đứng. Copilot dùng biểu thức canonical dễ đọc và mọi mô tả direction/asymptote phải xuất phát từ verified facts. Trig dạng hỗ trợ phải dùng nghiệm/cực trị giải tích thay vì sampling threshold. Frontend được phép dựng đường cong tạm thời chỉ khi tham số hợp lệ, nhưng không được suy đoán triệt tiêu bằng epsilon hoặc tạo giá trị thay thế.

Sampling không được dùng vòng `while` cộng float không giới hạn; số điểm phải cố định và phase/period vượt budget phải bị từ chối. Nghiệm trig không làm tròn trong domain model và dedup tolerance phải tỷ lệ theo chu kỳ. Rational cancellation phía frontend dùng tolerance tỷ lệ theo tích hệ số và khi đã xác định cancelled thì root tại hole luôn bị loại; renderer phải biểu diễn hole. Các dạng mũ tương đương `1/2**x`, `2**(-x)` và `2**(2*x)` vẫn thuộc ký pháp hỗ trợ nếu effective base hữu hạn và hợp lệ.

Tolerance trig phải dựa trên ULP và tỷ lệ chu kỳ, không có sàn tuyệt đối lớn hơn khoảng nghiệm; kiểm tra biên cửa sổ dùng cùng tolerance. Complexity guard phải ước lượng projected polynomial degree của toàn cây trước `expand`. Domain exclusions được dedup khi còn là nghiệm SymPy chính xác. RationalActivity phải sử dụng verified holes từ activity ban đầu, kể cả khi bốn hệ số không thể biểu diễn đầy đủ tổng phân thức; sau khi slider thay đổi mới dùng facts từ hệ số hiện tại.

Nếu biểu thức gốc chứa denominator phụ thuộc `x`, structural rational routing phải chạy trước mọi SymPy wildcard `match`; exclusions vẫn được giữ khi kết quả rút gọn là hằng hoặc polynomial. Trig chỉ được phân tích khi chu kỳ lớn hơn độ phân giải ULP tại phase/window; target nằm trong tolerance của ±1 được clamp trước nghiệm giải tích. So sánh proportional coefficients ở frontend phải normalize theo max magnitude trước phép nhân để tránh underflow/overflow.

Degree validation phải kiểm tra tử/mẫu của từng rational term trong expression tree trước khi cộng hoặc cancel; không chỉ kiểm tra fraction của tổng đã quy đồng. Mẫu số gốc rút gọn đồng nhất bằng 0 luôn bị từ chối. Ở trạng thái activity ban đầu, `holes`, `vertical_asymptotes` và domain do backend xác minh có quyền ưu tiên tuyệt đối; tọa độ y của hole lấy từ giới hạn/biểu thức rút gọn đã xác minh, không dùng near-equality hay fallback 0.

Trước mọi `sp.expand`, expression tree phi đa thức phải qua operation/node budget đủ để từ chối tích gây tăng tổ hợp; guard không được tự thực hiện phép khai triển. Mọi phép chia dùng cho target/tolerance phải kiểm tra numerator, denominator và kết quả hữu hạn trước clamp. Tất cả số dẫn xuất đưa vào Pydantic response phải hữu hạn; overflow/underflow làm mất nghĩa trả `MathEngineError`/HTTP 400, không serialize `null`.

## Verification

**Commands:**
- `backend/.venv/Scripts/python.exe -m pytest` -- toàn bộ backend tests pass.
- `npm test` trong `frontend/` -- toàn bộ frontend tests pass.
- `npm run build` trong `frontend/` -- TypeScript và Vite build thành công.

**Results (2026-08-21, review loop 1):**
- Backend focused: `151 passed, 1 warning`.
- Frontend focused: `36 passed`.
- Backend complete: `151 passed, 1 warning`.
- Frontend complete: `71 passed`.
- Frontend build: TypeScript và Vite thành công; còn cảnh báo dependency `jsxgraph` dùng `eval` nội bộ và bundle lớn.

**Results (2026-08-21, review loop 2):**
- Backend complete: `162 passed, 1 warning`.
- Frontend complete: `74 passed`.
- Frontend build: TypeScript và Vite thành công (`294 modules transformed`); còn cảnh báo dependency `jsxgraph` dùng `eval` nội bộ và bundle lớn.

**Results (2026-08-21, review loop 3):**
- Backend complete: `167 passed, 1 warning`.
- Frontend complete: `75 passed`.
- Frontend build: TypeScript và Vite thành công (`294 modules transformed`); còn cảnh báo dependency `jsxgraph` dùng `eval` nội bộ và bundle lớn.

**Results (2026-08-21, review loop 4):**
- Backend complete: `171 passed, 1 warning`.
- Frontend complete: `78 passed`.
- Frontend build: TypeScript và Vite thành công (`294 modules transformed`); còn cảnh báo dependency `jsxgraph` dùng `eval` nội bộ và bundle lớn.

**Results (2026-08-21, review loop 5):**
- Backend complete: `177 passed, 1 warning`.
- Frontend complete: `80 passed`.
- Frontend build: TypeScript và Vite thành công (`294 modules transformed`); còn cảnh báo dependency `jsxgraph` dùng `eval` nội bộ và bundle lớn.

**Results (2026-08-21, review loop 6):**
- Backend complete: `185 passed, 1 warning`.
- Frontend complete: `80 passed`.
- Frontend build: TypeScript và Vite thành công (`294 modules transformed`); còn cảnh báo dependency `jsxgraph` dùng `eval` nội bộ và bundle lớn.

**Closure patch:**
- Backend complete: `186 passed, 1 warning`.
- Frontend complete: `80 passed`.
- Frontend build và `git diff --check`: thành công.
- Review gate: không còn finding Critical/High.

## Suggested Review Order

**Trust boundary**

- Entry point điều phối parse, phân loại và finite response validation.
  [`math_service.py:968`](../../backend/app/services/math_service.py#L968)

- Parser allowlist giới hạn input trước mọi xử lý SymPy.
  [`math_service.py:201`](../../backend/app/services/math_service.py#L201)

- Expansion budget chặn polynomial và function-argument combinatorial DoS.
  [`math_service.py:248`](../../backend/app/services/math_service.py#L248)

**Mathematical correctness**

- Nghiệm lượng giác giải tích dùng finite, ULP và representability guards.
  [`math_service.py:363`](../../backend/app/services/math_service.py#L363)

- Rational analysis giữ denominator gốc, holes và domain exclusions.
  [`math_service.py:600`](../../backend/app/services/math_service.py#L600)

- Frontend ưu tiên verified holes trước facts suy ra từ slider.
  [`RationalActivity.tsx:52`](../../frontend/src/features/activities/RationalActivity.tsx#L52)

**Copilot integrity**

- Mọi Copilot facts được backend tái tạo từ expression.
  [`copilot_service.py:25`](../../backend/app/services/copilot_service.py#L25)

- Rule-based prose dùng direction và asymptotes đã xác minh.
  [`rule_based_copilot.py:149`](../../backend/app/providers/rule_based_copilot.py#L149)

**Invalid UI states**

- Activity giữ tham số thật, ẩn graph/facts và báo lỗi rõ.
  [`ActivityCanvas.tsx:85`](../../frontend/src/features/activities/ActivityCanvas.tsx#L85)

**Regression evidence**

- Security, complexity và finite-fact regressions bảo vệ boundary.
  [`test_math_service.py:324`](../../backend/tests/test_math_service.py#L324)

- API tests chứng minh client không thể giả mạo Copilot facts.
  [`test_api.py:118`](../../backend/tests/test_api.py#L118)
