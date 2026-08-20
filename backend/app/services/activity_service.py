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