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
    """Provider giả lập: sinh nội dung theo quy tắc cho hàm bậc hai/bậc nhất."""

    name = "rule_based"

    def __init__(self, delay_seconds: float = 0.5) -> None:
        self._delay = delay_seconds

    def suggest(self, request: CopilotRequest) -> CopilotSuggestion:
        time.sleep(self._delay)  # Mô phỏng độ trễ của model thật
        if request.activity_type == "linear_function":
            return self._linear(request)
        return self._quadratic(request)

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