"""RuleBasedCopilotProvider - đề xuất nội dung sư phạm theo quy tắc có kiểm soát.

Dùng để demo luồng Teacher Copilot mà không cần LLM. Mọi số liệu đều lấy từ
đặc trưng toán học do Math Engine tính (nguồn sự thật).
"""

from __future__ import annotations

import re
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


def _present_text(text: str, request: CopilotRequest) -> str:
    """Đổi ký hiệu x/y mặc định sang metadata trusted trong mọi prose/formula."""
    source = request.math.source_variable
    dependent = request.math.dependent_variable or "y"
    protected = [
        request.math.expression,
        request.math.axis,
        request.math.domain,
        *(request.math.asymptotes or []),
    ]
    placeholders: dict[str, str] = {}
    for index, value in enumerate(item for item in protected if item):
        placeholder = f"@@MATH_FACT_{index}@@"
        if value in text:
            text = text.replace(value, placeholder)
            placeholders[placeholder] = value
    text = text.replace("ax²", f"a{source}²").replace("bx", f"b{source}")
    text = re.sub(r"\bax\b", f"a{source}", text)
    text = re.sub(r"\bx\b", "@@SOURCE_VARIABLE@@", text)
    text = re.sub(r"\by\b", "@@DEPENDENT_VARIABLE@@", text)
    text = text.replace("@@SOURCE_VARIABLE@@", source)
    text = text.replace("@@DEPENDENT_VARIABLE@@", dependent)
    for placeholder, value in placeholders.items():
        text = text.replace(placeholder, value)
    return text


def _present_suggestion(
    suggestion: CopilotSuggestion, request: CopilotRequest
) -> CopilotSuggestion:
    return suggestion.model_copy(
        update={
            "summary": _present_text(suggestion.summary, request),
            "key_points": [
                _present_text(item, request) for item in suggestion.key_points
            ],
            "questions": [
                _present_text(item, request) for item in suggestion.questions
            ],
            "examples": [
                example.model_copy(
                    update={
                        "prompt": _present_text(example.prompt, request),
                        "solution": _present_text(example.solution, request),
                    }
                )
                for example in suggestion.examples
            ],
            "teaching_steps": [
                _present_text(item, request) for item in suggestion.teaching_steps
            ],
        }
    )


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
        return _present_suggestion(handler(request), request)

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
        holes = m.holes or []
        dependent = m.dependent_variable or "y"
        vertical_asymptotes = [
            item for item in asymptotes if item.startswith(f"{m.source_variable} =")
        ]
        horizontal_asymptotes = [
            item for item in asymptotes if item.startswith(f"{dependent} =")
        ]
        hole_text = " và ".join(_fmt(value) for value in holes)
        intercept_text = (
            f"Hàm số cắt trục hoành tại x = {root}."
            if m.root is not None
            else "Hàm số không cắt trục hoành."
        )
        if m.y_intercept is not None:
            intercept_text += f" Hàm số cắt trục tung tại y = {y_int}."
        domain_detail = (
            f"Hàm số có điểm khuyết tại x = {hole_text}."
            if holes
            else (
                "Hàm số không xác định tại các tiệm cận đứng đã nêu."
                if vertical_asymptotes
                else "Không có điểm loại trừ được cung cấp."
            )
        )
        geometry_detail = (
            "Sau khi triệt tiêu nhân tử, đồ thị là đường cong rút gọn có điểm khuyết."
            if holes
            else (
                "Đồ thị có các nhánh phân thức quanh tiệm cận đứng đã xác minh."
                if vertical_asymptotes
                else "Đồ thị được mô tả từ các giao điểm đã xác minh."
            )
        )
        key_points = [f"Tập xác định: {domain}. {domain_detail}"]
        if vertical_asymptotes:
            key_points.append(f"tiệm cận đứng: {', '.join(vertical_asymptotes)}.")
        elif holes:
            key_points.append(
                f"Điểm khuyết tại x = {hole_text}; nhân tử mẫu đã được triệt tiêu."
            )
        key_points.extend(
            f"Tiệm cận ngang đã xác minh: {asymptote}."
            for asymptote in horizontal_asymptotes
        )
        key_points.append(geometry_detail)
        return CopilotSuggestion(
            provider=self.name,
            summary=(
                f"Hàm số phân thức y = {expr} có tập xác định {domain}. "
                f"Đồ thị có tiệm cận: {asymptote_text}. "
                f"{intercept_text}"
            ),
            key_points=key_points,
            questions=[
                (
                    "Vì sao điểm bị loại khỏi tập xác định tạo thành một điểm khuyết?"
                    if holes
                    else "Tại sao hàm số không xác định tại giá trị của tiệm cận đứng?"
                ),
                (
                    f"Khi |x| lớn, đồ thị tiến gần {', '.join(horizontal_asymptotes)} như thế nào?"
                    if horizontal_asymptotes
                    else "Dựa trên các facts đã cho, hãy mô tả hành vi của đồ thị khi |x| lớn."
                ),
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
                    solution=(
                        f"Nghiệm: x = {root}."
                        if m.root is not None
                        else "Phương trình không có nghiệm trong tập xác định."
                    ),
                ),
            ],
            teaching_steps=[
                (
                    "Quan sát đồ thị rút gọn và xác định điểm khuyết."
                    if holes
                    else "Quan sát đồ thị: nhận xét hình dạng hai nhánh hyperbol."
                ),
                "Xác định tập xác định của hàm số.",
                (
                    "Xác định điểm khuyết hoặc các đường tiệm cận từ facts đã cho."
                    if holes or asymptotes
                    else "Xác định các giao điểm từ facts đã cho."
                ),
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
                f"Math Engine xác minh hàm số mũ y = {expr} {direction}, với cơ số hiệu dụng b = {base}; "
                f"đồ thị có tiệm cận ngang {asymptote} và cắt trục tung tại y = {y_int}."
            ),
            key_points=[
                f"Direction đã xác minh: hàm số {direction}; cơ số hiệu dụng b = {base}.",
                f"Tiệm cận ngang {asymptote}: đồ thị không bao giờ cắt đường này.",
                f"Đồ thị luôn cắt trục tung tại điểm (0; {y_int}).",
                root_point,
            ],
            questions=[
                f"Hàm đã được xác minh là {direction}; điều này thể hiện thế nào trên đồ thị?",
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
        direction = "đồng biến" if m.direction == "up" else "nghịch biến"
        return CopilotSuggestion(
            provider=self.name,
            summary=(
                f"Hàm số logarit y = {expr} có cơ số b = {base} và {direction}, tập xác định {domain}, "
                f"tiệm cận đứng {asymptote} và cắt trục hoành tại x = {root}."
            ),
            key_points=[
                f"Theo hệ số a và cơ số b = {base}, hàm số {direction}.",
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
