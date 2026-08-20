"""Dịch vụ tạo Activity từ kết quả Math Engine."""

from __future__ import annotations

from app.schemas.activity import (
    ActivityMath,
    ActivityModel,
    ActivitySource,
    ActivityStep,
    ActivityWidget,
)
from app.schemas.math import MathAnalyzeResponse
from app.services.math_service import analyze_expression


def build_activity(
    latex: str,
    expression: str,
    confidence: float,
    confirmed: bool = True,
) -> ActivityModel:
    """Tạo Activity theo loại biểu thức (bậc hai hoặc bậc nhất - phạm vi MVP)."""
    analysis = analyze_expression(expression)
    if analysis.kind == "quadratic":
        return build_quadratic_activity(latex, expression, confidence, confirmed)
    if analysis.kind == "linear":
        return build_linear_activity(latex, expression, confidence, confirmed)
    raise ValueError("MVP hỗ trợ hàm bậc hai và hàm bậc nhất.")


def build_linear_activity(
    latex: str,
    expression: str,
    confidence: float,
    confirmed: bool = True,
) -> ActivityModel:
    """Tạo Activity hàm bậc nhất (schemaVersion 1.0) từ biểu thức đã xác nhận."""
    analysis = analyze_expression(expression)
    if analysis.kind != "linear" or analysis.linear is None:
        raise ValueError("Activity hàm bậc nhất yêu cầu biểu thức bậc nhất hợp lệ.")
    l = analysis.linear
    return ActivityModel(
        schemaVersion="1.0",
        type="linear_function",
        source=ActivitySource(latex=latex, confidence=confidence, confirmed=confirmed),
        math=ActivityMath(
            expression=analysis.normalized_expression,
            a=l.a,
            b=l.b,
            y_intercept=l.y_intercept,
            root=l.root,
        ),
        widgets=[
            ActivityWidget(type="graph"),
            ActivityWidget(type="parameter_slider", parameters=["a", "b"]),
        ],
        steps=[
            ActivityStep(visible=["graph"]),
            ActivityStep(visible=["graph", "root"]),
        ],
    )


def build_quadratic_activity(
    latex: str,
    expression: str,
    confidence: float,
    confirmed: bool = True,
) -> ActivityModel:
    """Tạo Activity hàm bậc hai (schemaVersion 1.0) từ biểu thức đã xác nhận."""
    analysis = analyze_expression(expression)
    if analysis.kind != "quadratic" or analysis.quadratic is None:
        raise ValueError("Activity hàm bậc hai yêu cầu biểu thức bậc hai hợp lệ.")
    q = analysis.quadratic
    return ActivityModel(
        schemaVersion="1.0",
        type="quadratic_function",
        source=ActivitySource(latex=latex, confidence=confidence, confirmed=confirmed),
        math=ActivityMath(
            expression=analysis.normalized_expression,
            a=q.a,
            b=q.b,
            c=q.c,
            vertex=q.vertex,
            roots=q.roots,
            axis=q.axis,
            y_intercept=q.y_intercept,
            discriminant=q.discriminant,
            direction=q.direction,
        ),
        widgets=[
            ActivityWidget(type="graph"),
            ActivityWidget(type="parameter_slider", parameters=["a", "b", "c"]),
        ],
        steps=[
            ActivityStep(visible=["graph"]),
            ActivityStep(visible=["graph", "axis"]),
            ActivityStep(visible=["graph", "axis", "vertex", "roots"]),
        ],
    )