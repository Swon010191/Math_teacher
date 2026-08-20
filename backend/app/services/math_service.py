"""Math Engine - nguồn sự thật toán học của hệ thống.

Chỉ dùng SymPy để tính toán. LLM không bao giờ được dùng thay thế module này.
"""

from __future__ import annotations

import math
import tokenize

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

from app.schemas.math import (
    ExponentialFeatures,
    LinearFeatures,
    LogarithmicFeatures,
    MathAnalyzeResponse,
    QuadraticFeatures,
    RationalFeatures,
    TrigFeatures,
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


def _sample_points(
    expr: sp.Expr,
    center: float,
    range_: float | None = None,
) -> list[list[float]]:
    """Sinh điểm mẫu [x, y] quanh center để vẽ đồ thị (bỏ điểm không xác định)."""
    x = sp.Symbol("x")
    half = range_ if range_ is not None else _SAMPLE_RANGE
    points: list[list[float]] = []
    t = center - half
    while t <= center + half + 1e-9:
        try:
            y = float(expr.subs(x, t))
        except (TypeError, ValueError):
            y = float("nan")
        if math.isfinite(y):
            points.append([round(float(t), 4), round(y, 4)])
        t += _SAMPLE_STEP
    return points


def _match_trig(expr: sp.Expr) -> tuple[str, float, float, float, float] | None:
    """Khớp biểu thức dạng a*sin(bx+c)+d hoặc a*cos(bx+c)+d -> (func, a, b, c, d)."""
    x = sp.Symbol("x")
    a_w = sp.Wild("A", exclude=[x])
    b_w = sp.Wild("B", exclude=[x])
    c_w = sp.Wild("C", exclude=[x])
    d_w = sp.Wild("D", exclude=[x])
    patterns = (
        (a_w * sp.sin(b_w * x + c_w) + d_w, "sin"),
        (a_w * sp.cos(b_w * x + c_w) + d_w, "cos"),
        (a_w * sp.sin(b_w * x + c_w), "sin"),
        (a_w * sp.cos(b_w * x + c_w), "cos"),
    )
    for pat, func in patterns:
        m = expr.match(pat)
        if not m or a_w not in m or b_w not in m:
            continue
        try:
            a = float(m[a_w])
            b = float(m[b_w])
            c = float(m[c_w])
            d = float(m.get(d_w, 0))
        except (TypeError, ValueError):
            continue
        if a != 0 and b != 0:
            return func, a, b, c, d
    return None


def _trig_roots(expr: sp.Expr, center: float, period: float) -> list[float]:
    """Tìm nghiệm gần đúng của hàm lượng giác trong cửa sổ hai chu kỳ quanh center."""
    x = sp.Symbol("x")
    lo = center - period
    hi = center + period
    roots: list[float] = []
    prev_t = lo
    try:
        prev_y = float(expr.subs(x, lo))
    except (TypeError, ValueError):
        prev_y = float("nan")
    t = lo + 0.01
    while t <= hi + 1e-9:
        try:
            y = float(expr.subs(x, t))
        except (TypeError, ValueError):
            y = float("nan")
        if math.isfinite(y) and math.isfinite(prev_y):
            if prev_y == 0:
                roots.append(round(prev_t, 2))
            elif (prev_y > 0) != (y > 0):
                roots.append(round((prev_t + t) / 2, 2))
        prev_t = t
        prev_y = y
        t += 0.01
    deduped: list[float] = []
    for r in roots:
        if not deduped or abs(r - deduped[-1]) > 0.05:
            deduped.append(r)
    return deduped


def _match_exp(expr: sp.Expr) -> tuple[str, float, float, float] | None:
    """Khớp biểu thức dạng a*b^x + c hoặc a*e^(kx) + c -> (kind, a, base, c)."""
    x = sp.Symbol("x")
    a_w = sp.Wild("A", exclude=[x])
    b_w = sp.Wild("B", exclude=[x])
    c_w = sp.Wild("C", exclude=[x])
    k_w = sp.Wild("K", exclude=[x])
    patterns = (
        (a_w * b_w ** x + c_w, "pow"),
        (a_w * sp.exp(k_w * x) + c_w, "exp"),
        (a_w * b_w ** x, "pow"),
        (a_w * sp.exp(k_w * x), "exp"),
    )
    for pat, kind in patterns:
        m = expr.match(pat)
        if not m or a_w not in m:
            continue
        try:
            a = float(m[a_w])
            c = float(m.get(c_w, 0))
        except (TypeError, ValueError):
            continue
        if a == 0:
            continue
        if kind == "pow":
            base = m[b_w]
            if base == sp.E:
                base = math.e
            else:
                try:
                    base = float(base)
                except (TypeError, ValueError):
                    continue
            if base <= 0 or base == 1:
                continue
            return "pow", a, base, c
        try:
            k = float(m[k_w])
        except (TypeError, ValueError):
            continue
        if k == 0:
            continue
        return "exp", a, math.e ** k, c
    return None


def _match_log(expr: sp.Expr) -> tuple[float, float, float, float] | None:
    """Khớp biểu thức dạng a*log(x, base) + c -> (a, base, c, x_intercept)."""
    x = sp.Symbol("x")
    a_w = sp.Wild("A", exclude=[x])
    b_w = sp.Wild("B", exclude=[x])
    c_w = sp.Wild("C", exclude=[x])
    patterns = (
        (a_w * sp.log(x, b_w) + c_w, True),
        (a_w * sp.log(x, b_w), True),
        (a_w * sp.log(x) + c_w, False),
        (a_w * sp.log(x), False),
    )
    for pat, has_base in patterns:
        m = expr.match(pat)
        if not m or a_w not in m:
            continue
        try:
            a = float(m[a_w])
            c = float(m.get(c_w, 0))
            base = float(m[b_w]) if has_base else math.e
        except (TypeError, ValueError):
            continue
        if a == 0 or base <= 0 or base == 1:
            continue
        return a, base, c, float(base ** (-c / a))
    return None


def _analyze_rational(
    expr: sp.Expr,
    raw: str,
    latex: str,
    normalized: str,
) -> MathAnalyzeResponse:
    """Phân tích hàm phân thức bậc nhất/bậc nhất (ax + b)/(cx + d)."""
    x = sp.Symbol("x")
    num, den = sp.fraction(sp.cancel(expr))
    try:
        npoly = sp.Poly(num, x)
        dpoly = sp.Poly(den, x)
    except sp.PolynomialError as exc:
        raise MathEngineError(
            f"Chỉ hỗ trợ hàm phân thức bậc nhất/bậc nhất (ax + b)/(cx + d): {raw!r}"
        ) from exc
    if npoly.degree() > 1 or dpoly.degree() > 1:
        raise MathEngineError(
            f"Chỉ hỗ trợ hàm phân thức bậc nhất/bậc nhất (ax + b)/(cx + d): {raw!r}"
        )
    n_coeffs = npoly.all_coeffs()
    d_coeffs = dpoly.all_coeffs()
    a = float(n_coeffs[0]) if npoly.degree() == 1 else 0.0
    b = float(n_coeffs[1]) if npoly.degree() == 1 else float(n_coeffs[0])
    c = float(d_coeffs[0]) if dpoly.degree() == 1 else 0.0
    d = float(d_coeffs[1]) if dpoly.degree() == 1 else float(d_coeffs[0])

    poles = sorted(float(p) for p in sp.solve(sp.Eq(den, 0), x) if p.is_real)
    vertical_asymptotes = [f"x = {p:g}" for p in poles]
    horizontal_asymptote: str | None = None
    lim = sp.limit(expr, x, sp.oo)
    if lim.is_finite:
        horizontal_asymptote = f"y = {float(lim):g}"
    else:
        lim_neg = sp.limit(expr, x, -sp.oo)
        if lim_neg.is_finite:
            horizontal_asymptote = f"y = {float(lim_neg):g}"
    root = -b / a if a != 0 else None
    y_intercept = b / d if d != 0 else None
    domain = "x ≠ " + "; ".join(f"{p:g}" for p in poles) if poles else "R"
    center = 1.0 if any(abs(p) < 1e-9 for p in poles) else 0.0
    features = RationalFeatures(
        a=a,
        b=b,
        c=c,
        d=d,
        poles=poles,
        vertical_asymptotes=vertical_asymptotes,
        horizontal_asymptote=horizontal_asymptote,
        root=root,
        y_intercept=y_intercept,
        domain=domain,
        sample_points=_sample_points(expr, center),
    )
    return MathAnalyzeResponse(
        expression=raw,
        normalized_expression=normalized,
        kind="rational",
        latex=latex,
        rational=features,
    )


def _analyze_trig(
    expr: sp.Expr,
    match: tuple[str, float, float, float, float],
    raw: str,
    latex: str,
    normalized: str,
) -> MathAnalyzeResponse:
    """Phân tích hàm lượng giác y = a*sin(bx+c)+d hoặc a*cos(bx+c)+d."""
    func, a, b, c, d = match
    amplitude = abs(a)
    period = float(2 * sp.pi / abs(b))
    phase_shift = -c / b
    features = TrigFeatures(
        func=func,
        a=a,
        b=b,
        c=c,
        d=d,
        amplitude=amplitude,
        period=period,
        phase_shift=phase_shift,
        midline=d,
        max_value=amplitude + d,
        min_value=d - amplitude,
        roots=_trig_roots(expr, phase_shift, period),
        sample_points=_sample_points(expr, phase_shift, range_=period),
    )
    return MathAnalyzeResponse(
        expression=raw,
        normalized_expression=normalized,
        kind="trigonometric",
        latex=latex,
        trigonometric=features,
    )


def _analyze_exp(
    expr: sp.Expr,
    match: tuple[str, float, float, float],
    raw: str,
    latex: str,
    normalized: str,
) -> MathAnalyzeResponse:
    """Phân tích hàm mũ y = a*b^x + c."""
    kind, a, base, c = match
    x_intercept: float | None = None
    if a != 0 and c != 0 and -c / a > 0:
        x_intercept = float(sp.log(-c / a) / sp.log(base))
    features = ExponentialFeatures(
        a=a,
        b=base,
        c=c,
        base=base,
        direction="up" if base > 1 else "down",
        horizontal_asymptote=f"y = {c:g}",
        y_intercept=a + c,
        x_intercept=x_intercept,
        sample_points=_sample_points(expr, 0.0),
    )
    return MathAnalyzeResponse(
        expression=raw,
        normalized_expression=normalized,
        kind="exponential",
        latex=latex,
        exponential=features,
    )


def _analyze_log(
    expr: sp.Expr,
    match: tuple[float, float, float, float],
    raw: str,
    latex: str,
    normalized: str,
) -> MathAnalyzeResponse:
    """Phân tích hàm logarit y = a*log(x, base) + c."""
    a, base, c, x_intercept = match
    features = LogarithmicFeatures(
        a=a,
        b=base,
        c=c,
        base=base,
        domain="x > 0",
        vertical_asymptote="x = 0",
        x_intercept=x_intercept,
        sample_points=_sample_points(expr, 1.0),
    )
    return MathAnalyzeResponse(
        expression=raw,
        normalized_expression=normalized,
        kind="logarithmic",
        latex=latex,
        logarithmic=features,
    )


def _analyze_non_polynomial(
    expr: sp.Expr,
    raw: str,
    latex: str,
    normalized: str,
) -> MathAnalyzeResponse:
    """Phân tích biểu thức không phải đa thức: phân thức, lượng giác, mũ, logarit."""
    x = sp.Symbol("x")
    if expr.is_rational_function(x):
        return _analyze_rational(expr, raw, latex, normalized)
    trig = _match_trig(expr)
    if trig is not None:
        return _analyze_trig(expr, trig, raw, latex, normalized)
    exp_match = _match_exp(expr)
    if exp_match is not None:
        return _analyze_exp(expr, exp_match, raw, latex, normalized)
    log_match = _match_log(expr)
    if log_match is not None:
        return _analyze_log(expr, log_match, raw, latex, normalized)
    raise MathEngineError(
        "Loại hàm chưa được hỗ trợ (MVP: bậc hai, bậc nhất, phân thức, "
        "lượng giác sin/cos, mũ, logarit)."
    )


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
    expr = expr.subs(sp.Symbol("e"), sp.exp(1))
    latex = sp.latex(expr)
    normalized = sp.srepr(expr)

    try:
        poly = sp.Poly(expr, x)
    except sp.PolynomialError:
        return _analyze_non_polynomial(expr, raw, latex, normalized)
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
        "Phạm vi MVP chỉ hỗ trợ hàm bậc hai (y = ax^2 + bx + c), hàm bậc nhất, "
        "hàm phân thức, hàm lượng giác sin/cos, hàm mũ và hàm logarit."
    )