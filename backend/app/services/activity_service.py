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
from app.services.math_service import analyze_expression, solve_equation


def build_activity(
    latex: str,
    expression: str,
    confidence: float,
    confirmed: bool = True,
) -> ActivityModel:
    """Tạo Activity theo loại biểu thức (bậc hai, bậc nhất, phân thức, lượng giác, mũ, logarit, calculus, special)."""
    analysis = analyze_expression(expression)
    if analysis.kind == "quadratic":
        return build_quadratic_activity(latex, expression, confidence, confirmed, analysis)
    if analysis.kind == "linear":
        return build_linear_activity(latex, expression, confidence, confirmed, analysis)
    if analysis.kind == "rational":
        return build_rational_activity(latex, expression, confidence, confirmed, analysis)
    if analysis.kind == "trigonometric":
        return build_trig_activity(latex, expression, confidence, confirmed, analysis)
    if analysis.kind == "exponential":
        return build_exponential_activity(latex, expression, confidence, confirmed, analysis)
    if analysis.kind == "logarithmic":
        return build_logarithmic_activity(latex, expression, confidence, confirmed, analysis)
    if analysis.kind in ("calculus", "special"):
        return build_generic_activity(latex, expression, confidence, confirmed, analysis)
    raise ValueError("MVP hỗ trợ hàm bậc hai, bậc nhất, phân thức, lượng giác sin/cos, mũ, logarit, calculus và hàm đặc biệt.")


def build_linear_activity(
    latex: str,
    expression: str,
    confidence: float,
    confirmed: bool = True,
    analysis: MathAnalyzeResponse | None = None,
) -> ActivityModel:
    """Tạo Activity hàm bậc nhất (schemaVersion 1.0) từ biểu thức đã xác nhận."""
    analysis = analysis or analyze_expression(expression)
    if analysis.kind != "linear" or analysis.linear is None:
        raise ValueError("Activity hàm bậc nhất yêu cầu biểu thức bậc nhất hợp lệ.")
    l = analysis.linear
    canonical = analysis.canonical_expression or analysis.normalized_expression
    return ActivityModel(
        schemaVersion="1.0",
        type="linear_function",
        source=ActivitySource(latex=latex, confidence=confidence, confirmed=confirmed),
        math=ActivityMath(
            expression=canonical,
            source_variable=analysis.source_variable,
            dependent_variable=analysis.dependent_variable,
            a=l.a,
            b=l.b,
            y_intercept=l.y_intercept,
            root=l.root,
        ),
        solution=solve_equation(canonical, analysis.source_variable),
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
    analysis: MathAnalyzeResponse | None = None,
) -> ActivityModel:
    """Tạo Activity hàm bậc hai (schemaVersion 1.0) từ biểu thức đã xác nhận."""
    analysis = analysis or analyze_expression(expression)
    if analysis.kind != "quadratic" or analysis.quadratic is None:
        raise ValueError("Activity hàm bậc hai yêu cầu biểu thức bậc hai hợp lệ.")
    q = analysis.quadratic
    canonical = analysis.canonical_expression or analysis.normalized_expression
    return ActivityModel(
        schemaVersion="1.0",
        type="quadratic_function",
        source=ActivitySource(latex=latex, confidence=confidence, confirmed=confirmed),
        math=ActivityMath(
            expression=canonical,
            source_variable=analysis.source_variable,
            dependent_variable=analysis.dependent_variable,
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
        solution=solve_equation(canonical, analysis.source_variable),
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


def build_rational_activity(
    latex: str,
    expression: str,
    confidence: float,
    confirmed: bool = True,
    analysis: MathAnalyzeResponse | None = None,
) -> ActivityModel:
    """Tạo Activity hàm phân thức bậc nhất/bậc nhất (schemaVersion 1.0)."""
    analysis = analysis or analyze_expression(expression)
    if analysis.kind != "rational" or analysis.rational is None:
        raise ValueError("Activity hàm phân thức yêu cầu biểu thức (ax+b)/(cx+d) hợp lệ.")
    r = analysis.rational
    asymptotes = list(r.vertical_asymptotes)
    if r.horizontal_asymptote:
        asymptotes.append(r.horizontal_asymptote)
    return ActivityModel(
        schemaVersion="1.0",
        type="rational_function",
        source=ActivitySource(latex=latex, confidence=confidence, confirmed=confirmed),
        math=ActivityMath(
            expression=analysis.canonical_expression or analysis.normalized_expression,
            source_variable=analysis.source_variable,
            dependent_variable=analysis.dependent_variable,
            a=r.a,
            b=r.b,
            c=r.c,
            d=r.d,
            root=r.root,
            y_intercept=r.y_intercept,
            domain=r.domain,
            asymptotes=asymptotes,
            holes=r.holes,
        ),
        widgets=[
            ActivityWidget(type="graph"),
            ActivityWidget(type="parameter_slider", parameters=["a", "b", "c", "d"]),
        ],
        steps=[
            ActivityStep(visible=["graph"]),
            ActivityStep(visible=["graph", "vertical_asymptotes"]),
            ActivityStep(visible=["graph", "vertical_asymptotes", "horizontal_asymptote", "root"]),
        ],
    )


def build_trig_activity(
    latex: str,
    expression: str,
    confidence: float,
    confirmed: bool = True,
    analysis: MathAnalyzeResponse | None = None,
) -> ActivityModel:
    """Tạo Activity hàm lượng giác y = a*sin(bx+c)+d hoặc a*cos(bx+c)+d."""
    analysis = analysis or analyze_expression(expression)
    if analysis.kind != "trigonometric" or analysis.trigonometric is None:
        raise ValueError("Activity lượng giác yêu cầu biểu thức a*sin(bx+c)+d hoặc a*cos(bx+c)+d hợp lệ.")
    t = analysis.trigonometric
    return ActivityModel(
        schemaVersion="1.0",
        type="trig_function",
        source=ActivitySource(latex=latex, confidence=confidence, confirmed=confirmed),
        math=ActivityMath(
            expression=analysis.canonical_expression or analysis.normalized_expression,
            source_variable=analysis.source_variable,
            dependent_variable=analysis.dependent_variable,
            func=t.func,
            a=t.a,
            b=t.b,
            c=t.c,
            d=t.d,
            amplitude=t.amplitude,
            period=t.period,
            phase_shift=t.phase_shift,
            midline=t.midline,
            max_value=t.max_value,
            min_value=t.min_value,
            roots=t.roots,
        ),
        widgets=[
            ActivityWidget(type="graph"),
            ActivityWidget(type="parameter_slider", parameters=["a", "b", "c", "d"]),
        ],
        steps=[
            ActivityStep(visible=["graph"]),
            ActivityStep(visible=["graph", "midline"]),
            ActivityStep(visible=["graph", "midline", "max_min", "roots"]),
        ],
    )


def build_exponential_activity(
    latex: str,
    expression: str,
    confidence: float,
    confirmed: bool = True,
    analysis: MathAnalyzeResponse | None = None,
) -> ActivityModel:
    """Tạo Activity hàm mũ y = a*b^x + c."""
    analysis = analysis or analyze_expression(expression)
    if analysis.kind != "exponential" or analysis.exponential is None:
        raise ValueError("Activity hàm mũ yêu cầu biểu thức a*b^x + c hợp lệ.")
    e = analysis.exponential
    return ActivityModel(
        schemaVersion="1.0",
        type="exponential_function",
        source=ActivitySource(latex=latex, confidence=confidence, confirmed=confirmed),
        math=ActivityMath(
            expression=analysis.canonical_expression or analysis.normalized_expression,
            source_variable=analysis.source_variable,
            dependent_variable=analysis.dependent_variable,
            a=e.a,
            b=e.b,
            c=e.c,
            base=e.base,
            direction=e.direction,
            y_intercept=e.y_intercept,
            root=e.x_intercept,
            asymptotes=[e.horizontal_asymptote],
        ),
        widgets=[
            ActivityWidget(type="graph"),
            ActivityWidget(type="parameter_slider", parameters=["a", "b", "c"]),
        ],
        steps=[
            ActivityStep(visible=["graph"]),
            ActivityStep(visible=["graph", "asymptote"]),
            ActivityStep(visible=["graph", "asymptote", "y_intercept", "root"]),
        ],
    )


def build_logarithmic_activity(
    latex: str,
    expression: str,
    confidence: float,
    confirmed: bool = True,
    analysis: MathAnalyzeResponse | None = None,
) -> ActivityModel:
    """Tạo Activity hàm logarit y = a*log(x, base) + c."""
    analysis = analysis or analyze_expression(expression)
    if analysis.kind != "logarithmic" or analysis.logarithmic is None:
        raise ValueError("Activity hàm logarit yêu cầu biểu thức a*log(x, base) + c hợp lệ.")
    lg = analysis.logarithmic
    return ActivityModel(
        schemaVersion="1.0",
        type="logarithmic_function",
        source=ActivitySource(latex=latex, confidence=confidence, confirmed=confirmed),
        math=ActivityMath(
            expression=analysis.canonical_expression or analysis.normalized_expression,
            source_variable=analysis.source_variable,
            dependent_variable=analysis.dependent_variable,
            a=lg.a,
            b=lg.b,
            c=lg.c,
            base=lg.base,
            domain=lg.domain,
            root=lg.x_intercept,
            asymptotes=[lg.vertical_asymptote],
        ),
        widgets=[
            ActivityWidget(type="graph"),
            ActivityWidget(type="parameter_slider", parameters=["a", "b", "c"]),
        ],
        steps=[
            ActivityStep(visible=["graph"]),
            ActivityStep(visible=["graph", "asymptote"]),
            ActivityStep(visible=["graph", "asymptote", "root"]),
        ],
    )


def build_generic_activity(
    latex: str,
    expression: str,
    confidence: float,
    confirmed: bool = True,
    analysis: MathAnalyzeResponse | None = None,
) -> ActivityModel:
    """Tạo Activity cho calculus/special — graph + LaTeX giá trị."""
    analysis = analysis or analyze_expression(expression)
    if analysis.kind not in ("calculus", "special") or (analysis.calculus is None and analysis.special is None):
        raise ValueError("Activity generic yêu cầu calculus/special hợp lệ.")
    return ActivityModel(
        schemaVersion="1.0",
        type="generic_function" if analysis.kind == "calculus" else "special_function",
        source=ActivitySource(latex=latex, confidence=confidence, confirmed=confirmed),
        math=ActivityMath(
            expression=analysis.canonical_expression or analysis.normalized_expression,
            source_variable=analysis.source_variable,
            dependent_variable=analysis.dependent_variable,
        ),
        widgets=[
            ActivityWidget(type="graph"),
            ActivityWidget(type="formula"),
        ],
        steps=[
            ActivityStep(visible=["graph"]),
            ActivityStep(visible=["graph", "formula"]),
        ],
    )
