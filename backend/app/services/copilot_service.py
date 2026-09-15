"""Dịch vụ Teacher Copilot - chọn provider theo cài đặt (xem copilot_settings)."""

from __future__ import annotations

import math
import re

from app.providers.copilot_base import CopilotProvider
from app.providers.ollama_copilot import OllamaCopilotProvider
from app.providers.rule_based_copilot import RuleBasedCopilotProvider
from app.schemas.copilot import CopilotMathInput, CopilotRequest, CopilotSuggestion
from app.services.copilot_settings import (
    AVAILABLE_COPILOT_PROVIDERS,
    get_active_copilot_provider,
)
from app.services.math_service import analyze_expression


def _build_provider() -> CopilotProvider:
    name = get_active_copilot_provider()
    if name == "ollama":
        return OllamaCopilotProvider()
    if name == "rule_based":
        return RuleBasedCopilotProvider()
    raise ValueError(f"Provider không hợp lệ: {name!r}")


def _present_fact(
    value: str | None, source_variable: str, dependent_variable: str
) -> str | None:
    """Đổi symbol nội bộ trong facts hiển thị, không thay đổi phần số."""
    if value is None:
        return None
    value = re.sub(r"\bx\b", source_variable, value)
    return re.sub(r"\by\b", dependent_variable, value)


def _trusted_request(request: CopilotRequest) -> CopilotRequest:
    """Tính lại facts, loại activity và biểu thức hiển thị từ nguồn Math Engine."""
    analysis = analyze_expression(request.expression)
    source_variable = analysis.source_variable
    dependent_variable = analysis.dependent_variable or "y"
    common = {
        "expression": analysis.canonical_expression or request.expression,
        "source_variable": source_variable,
        "dependent_variable": analysis.dependent_variable,
    }
    if analysis.kind == "quadratic" and analysis.quadratic:
        activity_type = "quadratic_function"
        quadratic = analysis.quadratic.model_dump(exclude={"sample_points"})
        quadratic["axis"] = _present_fact(
            quadratic["axis"], source_variable, dependent_variable
        )
        facts = CopilotMathInput(
            **common, **quadratic
        )
    elif analysis.kind == "linear" and analysis.linear:
        activity_type = "linear_function"
        facts = CopilotMathInput(
            **common, **analysis.linear.model_dump(exclude={"sample_points"})
        )
    elif analysis.kind == "rational" and analysis.rational:
        r = analysis.rational
        activity_type = "rational_function"
        asymptotes = [
            _present_fact(item, source_variable, dependent_variable)
            for item in r.vertical_asymptotes
        ]
        if r.horizontal_asymptote:
            asymptotes.append(
                _present_fact(
                    r.horizontal_asymptote, source_variable, dependent_variable
                )
            )
        facts = CopilotMathInput(
            **common,
            a=r.a,
            b=r.b,
            c=r.c,
            d=r.d,
            root=r.root,
            y_intercept=r.y_intercept,
            holes=r.holes,
            asymptotes=asymptotes,
            domain=_present_fact(r.domain, source_variable, dependent_variable),
        )
    elif analysis.kind == "trigonometric" and analysis.trigonometric:
        activity_type = "trig_function"
        facts = CopilotMathInput(
            **common,
            **analysis.trigonometric.model_dump(exclude={"sample_points"}),
        )
    elif analysis.kind == "exponential" and analysis.exponential:
        exp = analysis.exponential
        activity_type = "exponential_function"
        facts = CopilotMathInput(
            **common,
            a=exp.a,
            b=exp.b,
            c=exp.c,
            base=exp.base,
            root=exp.x_intercept,
            y_intercept=exp.y_intercept,
            direction=exp.direction,
            asymptotes=[
                _present_fact(
                    exp.horizontal_asymptote, source_variable, dependent_variable
                )
            ],
        )
    elif analysis.kind == "logarithmic" and analysis.logarithmic:
        log = analysis.logarithmic
        activity_type = "logarithmic_function"
        direction = "up" if log.a / math.log(log.base) > 0 else "down"
        facts = CopilotMathInput(
            **common,
            a=log.a,
            b=log.b,
            c=log.c,
            base=log.base,
            root=log.x_intercept,
            direction=direction,
            domain=_present_fact(log.domain, source_variable, dependent_variable),
            asymptotes=[
                _present_fact(
                    log.vertical_asymptote, source_variable, dependent_variable
                )
            ],
        )
    else:  # pragma: no cover
        raise ValueError("Loại hàm không được Copilot hỗ trợ.")
    return request.model_copy(update={"activity_type": activity_type, "math": facts})


def suggest(request: CopilotRequest) -> CopilotSuggestion:
    """Đề xuất nội dung sư phạm cho Activity (giáo viên phải duyệt trước)."""
    trusted_request = _trusted_request(request)
    provider = _build_provider()
    try:
        return provider.suggest(trusted_request)
    except Exception as exc:  # noqa: BLE001 - báo rõ lỗi provider lên API
        raise RuntimeError(f"Lỗi Copilot ({provider.name}): {exc}") from exc
