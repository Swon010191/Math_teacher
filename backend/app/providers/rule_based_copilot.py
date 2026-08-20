"""RuleBasedCopilotProvider - đề xuất nội dung sư phạm theo quy tắc có kiểm soát.

Dùng để demo luồng Teacher Copilot mà không cần LLM. Mọi số liệu đều lấy từ
đặc trưng toán học do Math Engine tính (nguồn sự thật).
"""

from __future__ import annotations

import time

from app.providers.copilot_base import CopilotProvider
from app.schemas.copilot import CopilotExample, CopilotRequest, CopilotSuggestion


def _fmt(value: float | None) -> str:
    if value is None:
        return "?"
    text = f"{value:g}"
    return text


def _fmt_pair(pair: list[float] | None) -> str:
    if not pair:
        return "(?; ?)"
    return f"({_fmt(pair[0])}; {_fmt(pair[1])})"


def _fmt_roots(roots: list[float] | None) -> str:
    if not roots:
        return "không có nghiệm thực"
    return " và ".join(_fmt(r) for r in roots)


class RuleBasedCopilotProvider(CopilotProvider):
    """Provider giả lập: sinh nội dung theo quy tắc cho các loại hàm đã hỗ trợ."""

    name = "rule_based"

    def __init__(self, delay_seconds: float = 0.5) -> None:
        self._delay = delay_seconds

    def suggest(self, request: CopilotRequest) -> CopilotSuggestion:
        time.sleep(self._delay)  # Mô phỏng độ trễ của model thật
        handlers = {
            "linear_function": self._linear,
            "rational_function": self._rational,
            "trig_function": self._trig,
            "exponential_function": self._exponential,
            "logarithmic_function": self._logarithmic,
        }
        handler = handlers.get(request.activity_type, self._quadratic)
        return handler(request)

    def _quadratic(self, request: CopilotRequest) -> CopilotSuggestion:
        m = request.math
        expr = m.expression
        a = _fmt(m.a)
        vertex = _fmt_pair(m.vertex)
        axis = m.axis or "?"
        roots = _fmt_roots(m.roots)
        y_int = _fmt(m.y_intercept)
        direction = "lên trên" if m.direction == "up" else "xuống dưới"
        return CopilotSuggestion(
            provider=self.name,
            summary=(
                f"Hàm số bậc hai y = {expr} có đồ thị là một parabol bề lõm hướng {direction}. "
                f"Đỉnh của parabol là {vertex}, trục đối xứng {axis}, "
                f"cắt trục tung tại y = {y_int} và {roots}."
            ),
            key_points=[
                f"Dạng tổng quát y = ax² + bx + c, với hệ số a = {a} quyết định bề lõm (a > 0 bề lõm lên trên, a < 0 bề lõm xuống dưới).",
                f"Trục đối xứng {axis} chia parabol thành hai nhánh đối xứng.",
                f"Đỉnh I{vertex} là điểm cao nhất (a < 0) hoặc thấp nhất (a > 0) của đồ thị.",
                f"Phương trình y = 0 có nghiệm: {roots}.",
            ],
            questions=[
                "Dự đoán: parabol có bề lõm hướng lên hay xuống? Giải thích nhờ hệ số a.",
                "Giá trị lớn nhất/nhỏ nhất của hàm số là bao nhiêu, đạt tại x bằng mấy?",
                "Tìm các giá trị của x để y = 0 (nghiệm của phương trình).",
                "Nếu dịch parabol sang phải/trái 2 đơn vị thì đỉnh mới ở đâu?",
            ],
            examples=[
                CopilotExample(
                    prompt=f"Tìm đỉnh và trục đối xứng của parabol y = {expr}.",
                    solution=f"Đỉnh I{vertex}, trục đối xứng {axis}.",
                ),
                CopilotExample(
                    prompt=f"Giải phương trình y = 0 với y = {expr}.",
                    solution=f"Nghiệm: {roots}.",
                ),
            ],
            teaching_steps=[
                "Quan sát đồ thị: nhận xét bề lõm và hình dạng parabol.",
                "Xác định các hệ số a, b, c từ công thức hàm số.",
                "Tìm trục đối xứng và đỉnh của parabol.",
                "Tìm nghiệm và giao điểm với trục tung.",
                "Tổng kết và đặt câu hỏi vận dụng.",
            ],
            confidence=0.85,
        )

    def _linear(self, request: CopilotRequest) -> CopilotSuggestion:
        m = request.math
        expr = m.expression
        a = _fmt(m.a)
        b = _fmt(m.b)
        root = _fmt(m.root)
        y_int = _fmt(m.y_intercept)
        direction = "đồng biến" if (m.a or 0) > 0 else "nghịch biến"
        return CopilotSuggestion(
            provider=self.name,
            summary=(
                f"Hàm số bậc nhất y = {expr} có đồ thị là một đường thẳng, "
                f"hệ số góc a = {a} (hàm {direction}), "
                f"cắt trục tung tại y = {y_int} và cắt trục hoành tại x = {root}."
            ),
            key_points=[
                f"Dạng tổng quát y = ax + b với hệ số góc a = {a} và tung độ gốc b = {b}.",
                f"Hệ số góc a quyết định độ dốc: a > 0 hàm đồng biến, a < 0 hàm nghịch biến.",
                f"Đường thẳng cắt trục tung tại điểm (0; {y_int}).",
                f"Đường thẳng cắt trục hoành tại điểm ({root}; 0) (nghiệm của y = 0).",
            ],
            questions=[
                "Khi x tăng, giá trị y tăng hay giảm? Giải thích nhờ hệ số góc a.",
                "Đồ thị cắt trục tung tại điểm nào? Cắt trục hoành tại điểm nào?",
                "Vẽ đường thẳng bằng cách chỉ cần hai điểm: dùng giao điểm với hai trục.",
                "Nếu tăng hệ số a lên thì độ dốc của đường thẳng thay đổi thế nào?",
            ],
            examples=[
                CopilotExample(
                    prompt=f"Xác định hệ số góc và tung độ gốc của hàm số y = {expr}.",
                    solution=f"Hệ số góc a = {a}, tung độ gốc b = {b}.",
                ),
                CopilotExample(
                    prompt=f"Tìm nghiệm của phương trình y = 0 với y = {expr}.",
                    solution=f"Nghiệm x = {root}.",
                ),
            ],
            teaching_steps=[
                "Quan sát đồ thị: nhận xét hướng đi lên/xuống của đường thẳng.",
                "Xác định hệ số góc a và tung độ gốc b.",
                "Tìm giao điểm với trục tung và trục hoành.",
                "Vẽ đồ thị dựa trên hai giao điểm.",
                "Tổng kết và đặt câu hỏi vận dụng.",
            ],
            confidence=0.85,
        )

    def _rational(self, request: CopilotRequest) -> CopilotSuggestion:
        m = request.math
        expr = m.expression
        asymptotes = m.asymptotes or []
        root = _fmt(m.root)
        y_int = _fmt(m.y_intercept)
        domain = m.domain or "?"
        asymptote_text = ", ".join(asymptotes) if asymptotes else "không có"
        return CopilotSuggestion(
            provider=self.name,
            summary=(
                f"Hàm số phân thức y = {expr} có tập xác định {domain}. "
                f"Đồ thị có tiệm cận: {asymptote_text}. "
                f"Hàm số cắt trục hoành tại x = {root} và trục tung tại y = {y_int}."
            ),
            key_points=[
                f"Tập xác định: {domain} (hàm số không xác định tại tiệm cận đứng).",
                "Đường thẳng x = -d/c là tiệm cận đứng, đồ thị chia thành hai nhánh.",
                "Đường thẳng y = a/c là tiệm cận ngang: khi |x| rất lớn, đồ thị tiến gần đường này.",
                "Đồ thị hàm phân thức bậc nhất/bậc nhất là một hyperbol.",
            ],
            questions=[
                "Tại sao hàm số không xác định tại giá trị của tiệm cận đứng?",
                "Khi x rất lớn (hoặc rất nhỏ), giá trị của y tiến gần đến số nào?",
                "Đồ thị cắt trục tung và trục hoành tại những điểm nào?",
                "Nếu đổi dấu hệ số a thì vị trí các nhánh của đồ thị thay đổi thế nào?",
            ],
            examples=[
                CopilotExample(
                    prompt=f"Tìm tập xác định và các tiệm cận của hàm số y = {expr}.",
                    solution=f"Tập xác định {domain}; tiệm cận: {asymptote_text}.",
                ),
                CopilotExample(
                    prompt=f"Giải phương trình y = 0 với y = {expr}.",
                    solution=f"Nghiệm: x = {root}.",
                ),
            ],
            teaching_steps=[
                "Quan sát đồ thị: nhận xét hình dạng hai nhánh hyperbol.",
                "Xác định tập xác định của hàm số.",
                "Xác định tiệm cận đứng và tiệm cận ngang.",
                "Tìm nghiệm và giao điểm với trục tung.",
                "Tổng kết và đặt câu hỏi vận dụng.",
            ],
            confidence=0.85,
        )

    def _trig(self, request: CopilotRequest) -> CopilotSuggestion:
        m = request.math
        expr = m.expression
        func = m.func or "sin"
        amp = _fmt(m.amplitude)
        period = _fmt(m.period)
        midline = _fmt(m.midline)
        mx = _fmt(m.max_value)
        mn = _fmt(m.min_value)
        return CopilotSuggestion(
            provider=self.name,
            summary=(
                f"Hàm số lượng giác y = {expr} có đồ thị là đường hình sin (hàm {func}), "
                f"biên độ {amp}, chu kỳ {period}, dao động quanh đường trung bình y = {midline}. "
                f"Giá trị lớn nhất là {mx}, giá trị nhỏ nhất là {mn}."
            ),
            key_points=[
                f"Biên độ |a| = {amp} quyết định độ cao của đồ thị so với đường trung bình.",
                f"Chu kỳ T = 2π/|b| = {period}: đồ thị lặp lại sau mỗi chu kỳ.",
                f"Đường trung bình y = {midline} nằm chính giữa giá trị lớn nhất và nhỏ nhất.",
                f"Hàm số đạt giá trị lớn nhất {mx} và nhỏ nhất {mn}.",
            ],
            questions=[
                "Biên độ và chu kỳ của hàm số là bao nhiêu?",
                "Đồ thị đạt giá trị lớn nhất/nhỏ nhất tại những vị trí nào?",
                "Nếu tăng hệ số b thì chu kỳ thay đổi thế nào?",
                "Thay đổi d thì đường trung bình dịch chuyển ra sao?",
            ],
            examples=[
                CopilotExample(
                    prompt=f"Tìm biên độ và chu kỳ của hàm số y = {expr}.",
                    solution=f"Biên độ {amp}, chu kỳ {period}.",
                ),
                CopilotExample(
                    prompt=f"Tìm giá trị lớn nhất và nhỏ nhất của hàm số y = {expr}.",
                    solution=f"Giá trị lớn nhất {mx}, giá trị nhỏ nhất {mn}.",
                ),
            ],
            teaching_steps=[
                "Quan sát đồ thị: dạng sóng và đường trung bình.",
                "Xác định biên độ và chu kỳ của hàm số.",
                "Xác định giá trị lớn nhất, nhỏ nhất.",
                "Vẽ đồ thị trong một chu kỳ.",
                "Tổng kết và đặt câu hỏi vận dụng.",
            ],
            confidence=0.85,
        )

    def _exponential(self, request: CopilotRequest) -> CopilotSuggestion:
        m = request.math
        expr = m.expression
        base = _fmt(m.base)
        y_int = _fmt(m.y_intercept)
        root = _fmt(m.root)
        direction = "đồng biến" if m.direction == "up" else "nghịch biến"
        asymptote = (m.asymptotes or ["?"])[0]
        root_point = f"Hàm số cắt trục hoành tại x = {root}." if m.root is not None else "Hàm số không cắt trục hoành (phương trình y = 0 vô nghiệm)."
        return CopilotSuggestion(
            provider=self.name,
            summary=(
                f"Hàm số mũ y = {expr} có cơ số b = {base} nên hàm {direction}, "
                f"đồ thị có tiệm cận ngang {asymptote} và cắt trục tung tại y = {y_int}."
            ),
            key_points=[
                f"Cơ số b = {base}: b > 1 hàm đồng biến, 0 < b < 1 hàm nghịch biến.",
                f"Tiệm cận ngang {asymptote}: đồ thị không bao giờ cắt đường này.",
                f"Đồ thị luôn cắt trục tung tại điểm (0; {y_int}).",
                root_point,
            ],
            questions=[
                "Cơ số b lớn hơn 1 hay nhỏ hơn 1? Hàm số đồng biến hay nghịch biến?",
                "Đồ thị tiến gần đường thẳng nào khi x rất nhỏ (hoặc rất lớn)?",
                "Đồ thị cắt trục tung tại điểm nào?",
                "Nếu thay đổi hệ số c thì tiệm cận ngang dịch chuyển thế nào?",
            ],
            examples=[
                CopilotExample(
                    prompt=f"Xác định cơ số và tiệm cận ngang của hàm số y = {expr}.",
                    solution=f"Cơ số {base}, tiệm cận ngang {asymptote}.",
                ),
                CopilotExample(
                    prompt=f"Tìm giao điểm của đồ thị y = {expr} với trục tung.",
                    solution=f"Giao điểm (0; {y_int}).",
                ),
            ],
            teaching_steps=[
                "Quan sát đồ thị: nhận xét hàm đồng biến hay nghịch biến.",
                "Xác định cơ số và tiệm cận ngang.",
                "Tìm giao điểm với trục tung (và trục hoành nếu có).",
                "Vẽ đồ thị dựa trên tiệm cận và giao điểm.",
                "Tổng kết và đặt câu hỏi vận dụng.",
            ],
            confidence=0.85,
        )

    def _logarithmic(self, request: CopilotRequest) -> CopilotSuggestion:
        m = request.math
        expr = m.expression
        base = _fmt(m.base)
        root = _fmt(m.root)
        domain = m.domain or "?"
        asymptote = (m.asymptotes or ["?"])[0]
        return CopilotSuggestion(
            provider=self.name,
            summary=(
                f"Hàm số logarit y = {expr} có cơ số b = {base}, tập xác định {domain}, "
                f"tiệm cận đứng {asymptote} và cắt trục hoành tại x = {root}."
            ),
            key_points=[
                f"Cơ số b = {base}: b > 1 hàm đồng biến, 0 < b < 1 hàm nghịch biến.",
                f"Tập xác định {domain}: logarit chỉ xác định với giá trị dương.",
                f"Tiệm cận đứng {asymptote}: đồ thị tiến gần nhưng không cắt đường này.",
                f"Đồ thị luôn cắt trục hoành tại điểm ({root}; 0).",
            ],
            questions=[
                "Vì sao logarit chỉ xác định khi x > 0?",
                "Đồ thị tiến gần đường thẳng nào khi x tiến dần về 0?",
                "Đồ thị cắt trục hoành tại điểm nào?",
                "Cơ số b ảnh hưởng thế nào đến chiều biến thiên của hàm số?",
            ],
            examples=[
                CopilotExample(
                    prompt=f"Tìm tập xác định và tiệm cận đứng của hàm số y = {expr}.",
                    solution=f"Tập xác định {domain}, tiệm cận đứng {asymptote}.",
                ),
                CopilotExample(
                    prompt=f"Tìm giao điểm của đồ thị y = {expr} với trục hoành.",
                    solution=f"Giao điểm ({root}; 0).",
                ),
            ],
            teaching_steps=[
                "Quan sát đồ thị: nhận xét dáng điệu và chiều biến thiên.",
                "Xác định tập xác định của hàm số.",
                "Xác định tiệm cận đứng và giao điểm với trục hoành.",
                "Vẽ đồ thị dựa trên tiệm cận và giao điểm.",
                "Tổng kết và đặt câu hỏi vận dụng.",
            ],
            confidence=0.85,
        )