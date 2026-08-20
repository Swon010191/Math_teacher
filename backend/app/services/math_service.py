"""Math Engine - nguồn sự thật toán học của hệ thống.

Chỉ dùng SymPy để tính toán. LLM không bao giờ được dùng thay thế module này.
"""

from __future__ import annotations

import tokenize

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

from app.schemas.math import (
    LinearFeatures,
    MathAnalyzeResponse,
    QuadraticFeatures,
)

_SYMPIFY_ERRORS = (sp.SympifyError, TypeError, SyntaxError, tokenize.TokenError)

_TRANSFORMATIONS = standard_transformations + (
    convert_xor,
    implicit_multiplication_application,
)

_SAMPLE_RANGE = 5.0
_SAMPLE_STEP = 0.5


class MathEngineError(ValueError):
    """Lỗi phân tích biểu thức toán học."""


def normalize_expression(raw: str) -> str:
    """Chuẩn hóa biểu thức thô thành dạng SymPy.

    - Bỏ phần vế trái (y = ..., f(x) = ...) nếu có.
    - Chuyển ^ thành **, 4x thành 4*x, hỗ trợ viết tắt.
    """
    text = raw.strip()
    if not text:
        raise MathEngineError("Biểu thức trống.")
    for prefix in ("y=", "y =", "f(x)=", "f(x) =", "f(x):", "="):
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            break
    if not text:
        raise MathEngineError("Không tìm thấy vế phải của biểu thức.")
    try:
        expr = parse_expr(text, transformations=_TRANSFORMATIONS)
    except _SYMPIFY_ERRORS as exc:
        raise MathEngineError(f"Không phân tích được biểu thức: {raw!r}") from exc
    return sp.srepr(expr)


def _sample_points(expr: sp.Expr, center: float) -> list[list[float]]:
    """Sinh điểm mẫu [x, y] quanh center để vẽ đồ thị."""
    x = sp.Symbol("x")
    points: list[list[float]] = []
    t = center - _SAMPLE_RANGE
    while t <= center + _SAMPLE_RANGE + 1e-9:
        y = expr.subs(x, t)
        points.append([round(float(t), 4), round(float(y), 4)])
        t += _SAMPLE_STEP
    return points


def analyze_expression(raw: str) -> MathAnalyzeResponse:
    """Phân tích biểu thức, ưu tiên hàm bậc hai (phạm vi MVP)."""
    x = sp.Symbol("x")
    text = raw.strip()
    for prefix in ("y=", "y =", "f(x)=", "f(x) =", "f(x):"):
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            break
    try:
        expr = parse_expr(text, transformations=_TRANSFORMATIONS)
    except _SYMPIFY_ERRORS as exc:
        raise MathEngineError(f"Không phân tích được biểu thức: {raw!r}") from exc

    expr = sp.expand(expr)
    latex = sp.latex(expr)
    normalized = sp.srepr(expr)

    try:
        poly = sp.Poly(expr, x)
    except sp.PolynomialError as exc:
        raise MathEngineError(
            f"Biểu thức không phải đa thức theo x (MVP hỗ trợ bậc 1 và bậc 2): {raw!r}"
        ) from exc
    degree = poly.degree()
    coeffs = poly.all_coeffs()

    if degree == 2:
        a, b, c = (float(coeffs[i]) for i in range(3))
        d = b * b - 4 * a * c
        h = -b / (2 * a)
        k = -d / (4 * a)
        roots = sorted(
            float(r) for r in sp.solve(sp.Eq(expr, 0), x) if r.is_real
        )
        features = QuadraticFeatures(
            a=a,
            b=b,
            c=c,
            discriminant=d,
            vertex=[h, k],
            axis=f"x = {h:.4g}".replace(".0000", ""),
            roots=roots,
            y_intercept=c,
            direction="up" if a > 0 else "down",
            sample_points=_sample_points(expr, h),
        )
        return MathAnalyzeResponse(
            expression=raw,
            normalized_expression=normalized,
            kind="quadratic",
            latex=latex,
            quadratic=features,
        )

    if degree == 1:
        a, b = (float(coeffs[i]) for i in range(2))
        root = -b / a if a != 0 else None
        features = LinearFeatures(
            a=a,
            b=b,
            root=root,
            y_intercept=b,
            sample_points=_sample_points(expr, 0.0),
        )
        return MathAnalyzeResponse(
            expression=raw,
            normalized_expression=normalized,
            kind="linear",
            latex=latex,
            linear=features,
        )

    raise MathEngineError(
        "Phạm vi MVP chỉ hỗ trợ hàm bậc hai (y = ax^2 + bx + c) và hàm bậc nhất."
    )