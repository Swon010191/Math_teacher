"""Math Engine - nguồn sự thật toán học của hệ thống.

Chỉ dùng SymPy để tính toán. LLM không bao giờ được dùng thay thế module này.
"""

from __future__ import annotations

import math
import re
import sys
import tokenize
from dataclasses import dataclass

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

from app.providers.normalize import to_expression
from app.schemas.math import (
    ExponentialFeatures,
    LinearFeatures,
    LogarithmicFeatures,
    MathAnalyzeResponse,
    MathSolveResponse,
    QuadraticFeatures,
    RationalFeatures,
    SolveAnswer,
    SolveCase,
    SolveStep,
    SolveStepMetadata,
    TrigFeatures,
)

_SYMPIFY_ERRORS = (sp.SympifyError, TypeError, SyntaxError, tokenize.TokenError)

_TRANSFORMATIONS = standard_transformations + (
    convert_xor,
    implicit_multiplication_application,
)

_SAMPLE_RANGE = 5.0
_SAMPLE_STEP = 0.5
_SAMPLE_COUNT = 41
_MAX_TRIG_PERIOD = 10_000.0
_MAX_TRIG_PHASE = 1_000_000.0
_MAX_INPUT_LENGTH = 500
_MAX_TOKENS = 200
_MAX_EXPRESSION_NODES = 200
_MAX_VARIABLE_EXPONENT = 3
_MAX_EXPANSION_TERMS = 128
_MAX_EXPANSION_OPERATIONS = 256
_MAX_SYMBOLS = 16
_MAX_SYMBOL_LENGTH = 32

_X = sp.Symbol("x")
_ALLOWED_NAMES = {"x", "e", "pi", "sin", "cos", "log", "ln", "exp", "sqrt"}
_FUNCTION_NAMES = {"sin", "cos", "log", "ln", "exp", "sqrt"}
_LOCAL_DICT = {
    "x": _X,
    "e": sp.E,
    "pi": sp.pi,
    "sin": sp.sin,
    "cos": sp.cos,
    "log": sp.log,
    "ln": sp.log,
    "exp": sp.exp,
    "sqrt": sp.sqrt,
}
_GLOBAL_DICT = {
    "__builtins__": {},
    "Integer": sp.Integer,
    "Float": sp.Float,
    "Rational": sp.Rational,
    "Add": sp.Add,
    "Mul": sp.Mul,
    "Pow": sp.Pow,
}

_SUPERSCRIPT_DIGITS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
_SUBSCRIPT_CHARS = str.maketrans("₀₁₂₃₄₅₆₇₈₉ₑ", "0123456789e")

_LOGE_RE = re.compile(r"\bloge\s*\(")
_LOG_BASE_NAME_RE = re.compile(r"\blog(\d+)\s*\(")
_LG_NAME_RE = re.compile(r"\blg\s*\(")


class MathEngineError(ValueError):
    """Lỗi phân tích biểu thức toán học."""


@dataclass(frozen=True)
class _AnalysisInput:
    expression: sp.Expr
    source_variable: str
    dependent_variable: str | None
    canonical_expression: str


def _expand_superscripts(text: str) -> str:
    """Biến số mũ Unicode (², ³, ⁻², ⁿ) thành cú pháp ** của SymPy."""
    text = re.sub(
        r"⁻([⁰¹²³⁴⁵⁶⁷⁸⁹]+)",
        lambda m: "**-" + m.group(1).translate(_SUPERSCRIPT_DIGITS),
        text,
    )
    text = re.sub(
        r"([⁰¹²³⁴⁵⁶⁷⁸⁹]+)",
        lambda m: "**" + m.group(1).translate(_SUPERSCRIPT_DIGITS),
        text,
    )
    return text.replace("⁻", "-").replace("ⁿ", "**n")


def _normalize_glyphs(text: str) -> str:
    """Ngoặc nhọn {}, ký hiệu phép toán (· × ∗ ∙ ÷), chỉ số dưới -> cú pháp SymPy."""
    text = text.replace("{", "(").replace("}", ")")
    for glyph, repl in (("·", "*"), ("×", "*"), ("∗", "*"), ("∙", "*"), ("÷", "/")):
        text = text.replace(glyph, repl)
    return text.translate(_SUBSCRIPT_CHARS)


def _find_matching_paren(text: str, open_index: int) -> int:
    """Vị trí ngoặc đóng tương ứng với ngoặc mở tại open_index (-1 nếu lẻ)."""
    depth = 0
    for index in range(open_index, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return index
    return -1


def _replace_prefixed_call(
    text: str, pattern: re.Pattern[str], base_of: object
) -> str:
    """Thay logN(...)/lg(...) bằng log(..., base), chịu ngoặc lồng nhau."""
    guard = 0
    while guard < 1000:
        guard += 1
        match = pattern.search(text)
        if not match:
            break
        open_index = match.end() - 1
        close_index = _find_matching_paren(text, open_index)
        if close_index == -1:
            break
        inner = text[open_index + 1 : close_index]
        base = base_of(match) if callable(base_of) else base_of
        replacement = f"log({inner},{base})"
        text = text[: match.start()] + replacement + text[close_index + 1 :]
    return text


def _fix_log_forms(text: str) -> str:
    """log10(x) -> log(x,10); lg(x) -> log(x,10); log2(x) -> log(x,2); loge(x) -> log(x)."""
    text = _replace_prefixed_call(
        text, _LOG_BASE_NAME_RE, lambda m: m.group(1)
    )
    text = _replace_prefixed_call(text, _LG_NAME_RE, "10")
    text = _LOGE_RE.sub("log(", text)
    return text


def _prepare_text(raw: str) -> str:
    """Chuẩn hóa glyph/LaTeX nhưng chưa quyết định tập symbol hợp lệ."""
    text = raw.strip()
    if not text:
        raise MathEngineError("Biểu thức trống.")
    text = to_expression(text)
    text = _expand_superscripts(text)
    text = _normalize_glyphs(text)
    return _fix_log_forms(text)


def _preprocess_input(raw: str, variable_names: set[str] | None = None) -> str:
    """Chuẩn hóa chuỗi thô thành dạng SymPy chấp nhận được (chưa parse).

    - Bỏ phần vế trái (y = ..., f(x) = ...) nếu có.
    - LaTeX thô (\\frac, \\sqrt, \\cdot...) -> cú pháp SymPy.
    - Ngoặc nhọn {}, số mũ Unicode, ký hiệu · × ÷, lg()/log10()/log2().
    - Nếu không truyền variable_names, tự phát hiện để biểu thức nhiều
      biến (ví dụ t^2-1) được validate nhất quán với analyze/solve.
    """
    text = _prepare_text(raw)
    if variable_names is None:
        try:
            variable_names = _variable_names(text)
        except MathEngineError:
            variable_names = None
    _validate_input_tokens(text, variable_names)
    return text


def _validate_input_tokens(
    text: str, variable_names: set[str] | None = None
) -> None:
    """Chặn token ngoài ngôn ngữ toán học trước khi parser truy cập object."""
    if len(text) > _MAX_INPUT_LENGTH:
        raise MathEngineError("Biểu thức quá dài.")
    if "_" in text or "'" in text or '"' in text:
        raise MathEngineError("Biểu thức chứa ký tự không hợp lệ.")
    try:
        tokens = list(tokenize.generate_tokens(iter([text]).__next__))
    except (tokenize.TokenError, IndentationError) as exc:
        raise MathEngineError("Biểu thức không hợp lệ.") from exc
    if len(tokens) > _MAX_TOKENS:
        raise MathEngineError("Biểu thức quá phức tạp.")
    allowed_names = _ALLOWED_NAMES | (variable_names or set())
    allowed_ops = {"+", "-", "*", "/", "**", "^", "(", ")", ","}
    for index, token in enumerate(tokens):
        if token.type in {tokenize.ENDMARKER, tokenize.NEWLINE, tokenize.NL}:
            continue
        if token.type == tokenize.NAME:
            if token.string not in allowed_names:
                raise MathEngineError("Biểu thức chứa tên không được hỗ trợ.")
            next_token = tokens[index + 1] if index + 1 < len(tokens) else None
            if (
                next_token is not None
                and next_token.type == tokenize.OP
                and next_token.string == "("
                and token.string not in _FUNCTION_NAMES
            ):
                raise MathEngineError("Chỉ các hàm trong allowlist mới được gọi.")
            continue
        if token.type == tokenize.NUMBER:
            if len(re.sub(r"\D", "", token.string)) > 20:
                raise MathEngineError("Số trong biểu thức quá lớn.")
            try:
                value = float(token.string)
            except ValueError as exc:
                raise MathEngineError("Số trong biểu thức không hợp lệ.") from exc
            if not math.isfinite(value):
                raise MathEngineError("Số trong biểu thức phải hữu hạn.")
            continue
        if token.type == tokenize.OP and token.string in allowed_ops:
            continue
        raise MathEngineError("Biểu thức chứa token không hợp lệ.")


def _bounded_numeric_value(expr: sp.Expr, depth: int = 0) -> float:
    """Đánh giá cây số nhỏ theo giới hạn, không tạo số mũ khổng lồ."""
    if depth > 10:
        raise MathEngineError("Số mũ lồng quá sâu.")
    if isinstance(expr, sp.Number):
        try:
            value = float(expr)
        except (TypeError, ValueError, OverflowError) as exc:
            raise MathEngineError("Giá trị số phải là số thực hữu hạn.") from exc
    elif isinstance(expr, sp.Add):
        value = sum(_bounded_numeric_value(arg, depth + 1) for arg in expr.args)
    elif isinstance(expr, sp.Mul):
        value = math.prod(_bounded_numeric_value(arg, depth + 1) for arg in expr.args)
    elif isinstance(expr, sp.Pow):
        base = _bounded_numeric_value(expr.base, depth + 1)
        exponent = _bounded_numeric_value(expr.exp, depth + 1)
        if abs(exponent) > 100:
            raise MathEngineError("Số mũ quá lớn.")
        if base != 0 and exponent * math.log(abs(base)) > math.log(sys.float_info.max):
            raise MathEngineError("Lũy thừa vượt giới hạn hữu hạn.")
        try:
            value = base**exponent
        except (OverflowError, ZeroDivisionError, ValueError) as exc:
            raise MathEngineError("Lũy thừa không hợp lệ.") from exc
    else:
        raise MathEngineError("Số mũ phải là biểu thức số hữu hạn.")
    if isinstance(value, complex) or not math.isfinite(value):
        raise MathEngineError("Giá trị số phải hữu hạn.")
    return value


def _parse_limited(
    text: str, symbols: dict[str, sp.Symbol] | None = None
) -> sp.Expr:
    """Parse trong namespace giới hạn và hậu kiểm trước mọi phép expand."""
    try:
        local_dict = dict(_LOCAL_DICT)
        if symbols:
            local_dict.update(symbols)
        expr = parse_expr(
            text,
            local_dict=local_dict,
            global_dict=_GLOBAL_DICT,
            transformations=_TRANSFORMATIONS,
            evaluate=False,
        )
    except (_SYMPIFY_ERRORS, AttributeError, NameError, ValueError) as exc:
        raise MathEngineError("Biểu thức không hợp lệ hoặc không được hỗ trợ.") from exc
    allowed_symbols = set(symbols.values()) if symbols else {_X}
    if not isinstance(expr, sp.Expr) or not expr.free_symbols.issubset(allowed_symbols):
        raise MathEngineError("Biểu thức chứa symbol không được hỗ trợ.")
    nodes = list(sp.preorder_traversal(expr))
    if len(nodes) > _MAX_EXPRESSION_NODES:
        raise MathEngineError("Biểu thức quá phức tạp.")
    for node in nodes:
        if isinstance(node, sp.Number) and not math.isfinite(float(node)):
            raise MathEngineError("Giá trị số phải hữu hạn.")
        if isinstance(node, sp.Pow) and node.exp.is_number:
            exponent = _bounded_numeric_value(node.exp)
            if node.base.free_symbols & allowed_symbols and (
                not exponent.is_integer() or abs(exponent) > _MAX_VARIABLE_EXPONENT
            ):
                raise MathEngineError("Số mũ của biểu thức chứa biến vượt giới hạn.")
    return expr


def _variable_names(text: str) -> set[str]:
    """Lấy identifier symbol; tên hàm/hằng vẫn thuộc allowlist cố định."""
    try:
        tokens = list(tokenize.generate_tokens(iter([text]).__next__))
    except (tokenize.TokenError, IndentationError) as exc:
        raise MathEngineError("Biểu thức không hợp lệ.") from exc
    names = {
        token.string
        for token in tokens
        if token.type == tokenize.NAME and token.string not in _ALLOWED_NAMES
    }
    if len(names) > _MAX_SYMBOLS:
        raise MathEngineError("Biểu thức chứa quá nhiều biến.")
    if any(
        len(name) > _MAX_SYMBOL_LENGTH
        or re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", name) is None
        for name in names
    ):
        raise MathEngineError("Tên biến phải là identifier ASCII an toàn.")
    return names


def _parse_symbolic_text(text: str) -> tuple[sp.Expr, dict[str, sp.Symbol]]:
    names = _variable_names(text)
    symbols = {name: sp.Symbol(name, real=True) for name in names}
    if "x" in text and "x" not in names:
        # x belongs to the legacy allowlist and must still be included dynamically.
        try:
            if any(
                token.type == tokenize.NAME and token.string == "x"
                for token in tokenize.generate_tokens(iter([text]).__next__)
            ):
                symbols["x"] = _X
        except tokenize.TokenError as exc:
            raise MathEngineError("Biểu thức không hợp lệ.") from exc
    _validate_input_tokens(text, set(symbols))
    return _parse_limited(text, symbols), symbols


def _function_marker(text: str) -> tuple[str, str | None] | None:
    """Nhận tên biến phụ thuộc hoặc chữ ký hàm một biến."""
    identifier = r"[A-Za-z][A-Za-z0-9]*"
    match = re.fullmatch(rf"({identifier})\s*\(\s*({identifier})\s*\)", text)
    if match:
        return match.group(1), match.group(2)
    if re.fullmatch(identifier, text):
        return text, None
    return None


def _parse_analysis_input(raw: str) -> _AnalysisInput:
    """Parse định nghĩa hàm rồi ánh xạ duy nhất biến nguồn về symbol nội bộ x."""
    dependent: str | None = None
    source_hint: str | None = None
    body_raw = raw
    if raw.count("=") > 1:
        raise MathEngineError("Biểu thức chỉ được chứa tối đa một dấu '='.")
    if "=" in raw:
        left, right = (part.strip() for part in raw.split("=", 1))
        left_marker = _function_marker(left)
        right_marker = _function_marker(right)
        if (left_marker is None) == (right_marker is None):
            raise MathEngineError(
                "Định nghĩa hàm yêu cầu đúng một vế là tên biến hoặc dạng f(t)."
            )
        if left_marker is not None:
            dependent, source_hint = left_marker
            body_raw = right
        else:
            dependent, source_hint = right_marker  # type: ignore[misc]
            body_raw = left
    text = _prepare_text(body_raw)
    parsed, symbols = _parse_symbolic_text(text)
    names = sorted(symbol.name for symbol in parsed.free_symbols)
    if source_hint is not None and source_hint not in names:
        raise MathEngineError("Biến trong định nghĩa hàm phải xuất hiện ở vế phải.")
    if len(names) != 1:
        raise MathEngineError("Phân tích hàm yêu cầu đúng một biến nguồn.")
    source = source_hint or names[0]
    if parsed.is_Symbol and len(source) > 1:
        # Một tên riêng nhiều ký tự (ví dụ "abc") gần như luôn là lỗi
        # gõ/nhận dạng, không phải hàm số. Tên một ký tự (x, t, u...)
        # vẫn được chấp nhận làm hàm đồng nhất.
        raise MathEngineError(
            "Biểu thức chỉ là một tên riêng, chưa phải hàm số hay phương trình."
        )
    if dependent == source:
        raise MathEngineError("Biến nguồn phải khác biến phụ thuộc.")
    if source != names[0]:
        raise MathEngineError("Vế phải chứa biến khác biến nguồn của hàm.")
    source_symbol = symbols.get(source, _X if source == "x" else None)
    if source_symbol is None:
        raise MathEngineError("Không xác định được biến nguồn.")
    if source == "x":
        internal = parsed
    else:
        tokens = tokenize.generate_tokens(iter([text]).__next__)
        internal_text = tokenize.untokenize(
            (
                token.type,
                "x"
                if token.type == tokenize.NAME and token.string == source
                else token.string,
            )
            for token in tokens
        )
        _validate_input_tokens(internal_text)
        internal = _parse_limited(internal_text)
    # Canonicalization runs only after analysis budgets pass; cancel() can be
    # expensive on an intentionally adversarial tree.
    canonical = sp.sstr(parsed)
    return _AnalysisInput(internal, source, dependent, canonical)


def _safe_approximation(value: sp.Expr) -> float | None:
    if not value.is_number or value.is_real is not True:
        return None
    return _finite_float(sp.N(value, 15), "Nghiệm gần đúng")


def _solve_answer(value: sp.Expr, condition: str | None = None) -> SolveAnswer:
    value = sp.simplify(value)
    return SolveAnswer(
        exact=sp.sstr(value),
        latex=sp.latex(value),
        approximate=_safe_approximation(value),
        condition=condition,
    )


def _solve_step(
    expression: str,
    explanation: str,
    latex: str,
    kind: str,
    *,
    rule: str | None = None,
    values: dict[str, sp.Expr | str] | None = None,
) -> SolveStep:
    """Build a display step with exact, machine-readable SymPy values."""
    return SolveStep(
        expression=expression,
        explanation=explanation,
        latex=latex,
        metadata=SolveStepMetadata(
            kind=kind,
            rule=rule,
            values={
                key: sp.sstr(value) if isinstance(value, sp.Basic) else value
                for key, value in (values or {}).items()
            },
        ),
    )


def solve_equation(raw: str, solve_for: str | None = None) -> MathSolveResponse:
    """Giải đa thức bậc nhất/hai bằng SymPy trong parser và budget giới hạn."""
    if raw.count("=") > 1:
        raise MathEngineError("Phương trình chỉ được chứa tối đa một dấu '='.")
    left_raw, right_raw = (
        (part.strip() for part in raw.split("=", 1))
        if "=" in raw
        else (raw, "0")
    )
    left_text = _prepare_text(left_raw)
    right_text = _prepare_text(right_raw)
    combined = f"({left_text})-({right_text})"
    difference, symbols = _parse_symbolic_text(combined)
    variables = sorted(symbols)
    if solve_for is not None and re.fullmatch(
        r"[A-Za-z][A-Za-z0-9]*", solve_for
    ) is None:
        raise MathEngineError("solve_for phải là identifier ASCII an toàn.")
    if solve_for is None:
        if len(variables) > 1:
            raise MathEngineError(
                "Phương trình có nhiều biến; cần truyền solve_for. "
                f"variables: {', '.join(variables)}"
            )
        if not variables:
            raise MathEngineError("Phương trình không chứa biến để giải.")
        solve_for = variables[0]
    if solve_for not in symbols:
        raise MathEngineError(
            f"solve_for phải thuộc danh sách variables: {', '.join(variables)}"
        )
    target = symbols[solve_for]
    _validate_expansion_budget(difference)
    expanded = _exactify_floats(sp.expand(difference))
    try:
        polynomial = sp.Poly(expanded, target)
    except sp.PolynomialError as exc:
        raise MathEngineError("Chỉ hỗ trợ phương trình đa thức theo solve_for.") from exc
    degree_value = polynomial.degree()
    degree = 0 if degree_value == sp.S.NegativeInfinity else int(degree_value)
    if degree > 2:
        raise MathEngineError("Chỉ hỗ trợ phương trình bậc nhất và bậc hai.")

    left_expr = _parse_limited(left_text, symbols)
    right_expr = _parse_limited(right_text, symbols)
    canonical_equation = (
        f"{sp.sstr(sp.cancel(left_expr))} = {sp.sstr(sp.cancel(right_expr))}"
    )
    steps = [
        _solve_step(
            canonical_equation,
            "Ghi lại phương trình và xác định miền giải là số thực.",
            f"{sp.latex(sp.cancel(left_expr))} = {sp.latex(sp.cancel(right_expr))}",
            "equation",
            rule="original_equation",
            values={"variable": solve_for},
        ),
        _solve_step(
            f"{sp.sstr(expanded)} = 0",
            f"Chuyển tất cả hạng tử sang một vế và thu gọn theo {solve_for}.",
            f"{sp.latex(expanded)} = 0",
            "transformation",
            rule="standard_form",
            values={"standard_form": expanded},
        ),
    ]
    answers: list[SolveAnswer] = []
    cases: list[SolveCase] = []
    verified = False
    final_latex = ""

    if degree == 0:
        steps.append(
            _solve_step(
                f"c = {sp.sstr(expanded)}",
                f"Phương trình không còn hạng tử chứa {solve_for}; hệ số hằng là c.",
                f"c = {sp.latex(expanded)}",
                "coefficient_identification",
                rule="constant_equation",
                values={"c": expanded},
            )
        )
        if expanded == 0:
            status, classification = "infinite_solutions", "identity"
            explanation = "Hai vế đồng nhất; mọi giá trị thực đều là nghiệm."
        elif expanded.free_symbols:
            status, classification = "conditional", "degenerate"
            cases = [
                SolveCase(condition=f"{sp.sstr(expanded)} = 0", status="infinite_solutions"),
                SolveCase(condition=f"{sp.sstr(expanded)} != 0", status="no_solution"),
            ]
            explanation = "Kết quả phụ thuộc vào giá trị của các tham số."
        else:
            status, classification = "no_solution", "contradiction"
            explanation = "Hai vế thu gọn thành một mệnh đề sai."
        verified = True
        final_latex = rf"\text{{{status.replace('_', ' ')}}}"
        steps.append(
            _solve_step(
                status,
                explanation,
                final_latex,
                "answer",
                rule=classification,
                values={"status": status},
            )
        )
        steps.append(
            _solve_step(
                (
                    "; ".join(f"{case.condition}: {case.status}" for case in cases)
                    if cases
                    else f"{sp.sstr(expanded)} = 0 is {str(expanded == 0).lower()}"
                ),
                "Kiểm tra chính xác mệnh đề hằng và các trường hợp tham số.",
                (
                    r"\text{Xét các trường hợp tham số}"
                    if cases
                    else f"{sp.latex(expanded)} = 0"
                ),
                "verification",
                rule="exact_simplification",
                values={
                    "remainder": expanded,
                    "case_count": str(len(cases)),
                    "verified": "true",
                },
            )
        )
    else:
        coefficients = polynomial.all_coeffs()
        leading = coefficients[0]
        classification = "linear" if degree == 1 else "quadratic"
        leading_uncertain = leading.is_zero is None
        discriminant: sp.Expr | None = None
        if degree == 2:
            discriminant = sp.simplify(coefficients[1] ** 2 - 4 * leading * coefficients[2])
            coefficient_values = dict(zip(("a", "b", "c"), coefficients))
        else:
            coefficient_values = dict(zip(("a", "b"), coefficients))
        coefficient_text = ", ".join(
            f"{name} = {sp.sstr(value)}" for name, value in coefficient_values.items()
        )
        coefficient_latex = r",\quad ".join(
            f"{name} = {sp.latex(value)}" for name, value in coefficient_values.items()
        )
        steps.append(
            _solve_step(
                coefficient_text,
                f"Đối chiếu với dạng chuẩn của phương trình {classification}.",
                coefficient_latex,
                "coefficient_identification",
                rule=f"{classification}_coefficients",
                values=coefficient_values,
            )
        )

        if degree == 1:
            constant = coefficients[1]
            root = sp.simplify(-constant / leading)
            real_roots = [root]
            steps.append(
                _solve_step(
                    f"{sp.sstr(leading * target)} = {sp.sstr(-constant)}",
                    f"Chuyển hạng tử tự do sang vế phải để cô lập hạng tử chứa {solve_for}.",
                    f"{sp.latex(leading * target)} = {sp.latex(-constant)}",
                    "transformation",
                    rule="addition_property_of_equality",
                    values={"a": leading, "b": constant},
                )
            )
            steps.append(
                _solve_step(
                    f"{solve_for} = -b/a = {sp.sstr(root)}",
                    "Chia hai vế cho hệ số a (với a khác 0).",
                    rf"{sp.latex(target)} = -\frac{{{sp.latex(constant)}}}{{{sp.latex(leading)}}} = {sp.latex(root)}",
                    "formula",
                    rule="linear_formula",
                    values={"a": leading, "b": constant, "result": root},
                )
            )
        else:
            linear_coefficient, constant = coefficients[1:]
            assert discriminant is not None
            steps.append(
                _solve_step(
                    f"discriminant = b**2 - 4*a*c = {sp.sstr(discriminant)}",
                    "Tính biệt thức để xác định số nghiệm thực.",
                    rf"\Delta = {sp.latex(linear_coefficient)}^2 - 4({sp.latex(leading)})({sp.latex(constant)}) = {sp.latex(discriminant)}",
                    "discriminant",
                    rule="quadratic_discriminant",
                    values={"a": leading, "b": linear_coefficient, "c": constant, "discriminant": discriminant},
                )
            )
            if discriminant.is_negative is True:
                real_roots = []
            else:
                minus_root = sp.simplify(
                    (-linear_coefficient - sp.sqrt(discriminant)) / (2 * leading)
                )
                plus_root = sp.simplify(
                    (-linear_coefficient + sp.sqrt(discriminant)) / (2 * leading)
                )
                real_roots = [minus_root]
                if sp.simplify(plus_root - minus_root) != 0:
                    real_roots.append(plus_root)
            formula_result = ", ".join(sp.sstr(root) for root in real_roots) or "no real root"
            steps.append(
                _solve_step(
                    f"{solve_for} = (-b +/- sqrt(discriminant))/(2*a): {formula_result}",
                    "Áp dụng công thức nghiệm khi a khác 0 và biệt thức không âm.",
                    (
                        rf"{sp.latex(target)} = \frac{{-{sp.latex(linear_coefficient)} \pm "
                        rf"\sqrt{{{sp.latex(discriminant)}}}}}{{2({sp.latex(leading)})}}"
                    ),
                    "formula",
                    rule="quadratic_formula",
                    values={"discriminant": discriminant, "result": formula_result},
                )
            )
        condition: str | None = None
        if leading_uncertain:
            condition = f"{sp.sstr(leading)} != 0"
        if discriminant is not None and discriminant.is_nonnegative is None:
            disc_condition = f"{sp.sstr(discriminant)} > 0"
            condition = f"{condition} and {disc_condition}" if condition else disc_condition
        answers = [_solve_answer(root, condition) for root in real_roots]
        verified = all(sp.simplify(expanded.subs(target, root)) == 0 for root in real_roots)
        if leading_uncertain or (discriminant is not None and discriminant.is_nonnegative is None):
            status = "conditional"
            if answers:
                cases.append(SolveCase(condition=condition or "true", status="solved", answers=answers))
            if discriminant is not None and discriminant.is_nonnegative is None:
                zero_condition = f"{sp.sstr(discriminant)} = 0"
                if leading_uncertain:
                    zero_condition = f"{sp.sstr(leading)} != 0 and {zero_condition}"
                repeated_root = sp.simplify(-coefficients[1] / (2 * leading))
                cases.append(
                    SolveCase(
                        condition=zero_condition,
                        status="solved",
                        answers=[_solve_answer(repeated_root, zero_condition)],
                    )
                )
                cases.append(
                    SolveCase(
                        condition=f"{sp.sstr(discriminant)} < 0",
                        status="no_solution",
                    )
                )
            if leading_uncertain:
                if degree == 1:
                    constant = coefficients[1]
                    cases.extend(
                        [
                            SolveCase(
                                condition=(
                                    f"{sp.sstr(leading)} = 0 and "
                                    f"{sp.sstr(constant)} = 0"
                                ),
                                status="infinite_solutions",
                            ),
                            SolveCase(
                                condition=(
                                    f"{sp.sstr(leading)} = 0 and "
                                    f"{sp.sstr(constant)} != 0"
                                ),
                                status="no_solution",
                            ),
                        ]
                    )
                else:
                    linear_condition = (
                        f"{sp.sstr(leading)} = 0 and "
                        f"{sp.sstr(linear_coefficient)} != 0"
                    )
                    cases.extend(
                        [
                            SolveCase(
                                condition=linear_condition,
                                status="solved",
                                answers=[
                                    _solve_answer(
                                        -constant / linear_coefficient,
                                        linear_condition,
                                    )
                                ],
                            ),
                            SolveCase(
                                condition=(
                                    f"{sp.sstr(leading)} = 0 and "
                                    f"{sp.sstr(linear_coefficient)} = 0 and "
                                    f"{sp.sstr(constant)} = 0"
                                ),
                                status="infinite_solutions",
                            ),
                            SolveCase(
                                condition=(
                                    f"{sp.sstr(leading)} = 0 and "
                                    f"{sp.sstr(linear_coefficient)} = 0 and "
                                    f"{sp.sstr(constant)} != 0"
                                ),
                                status="no_solution",
                            ),
                        ]
                    )
        elif answers:
            status = "solved"
        else:
            status = "no_solution"
        explanation = (
            f"Giải công thức {classification} theo {solve_for}; chỉ giữ nghiệm thực."
        )
        final_latex = (
            ", ".join(sp.latex(sp.Eq(target, root)) for root in real_roots)
            if real_roots
            else r"\text{no real solution}"
        )
        if cases:
            steps.append(
                _solve_step(
                    "; ".join(f"{case.condition}: {case.status}" for case in cases),
                    "Tách các trường hợp tham số có thể làm giảm bậc hoặc đổi số nghiệm thực.",
                    r"\text{Xét các trường hợp tham số}",
                    "case_analysis",
                    rule="degenerate_parameter_cases",
                    values={"case_count": str(len(cases))},
                )
            )
        answer_values: dict[str, sp.Expr | str] = {
            "status": status,
            "answer_count": str(len(answers)),
        }
        answer_values.update(
            {f"solution_{index}": root for index, root in enumerate(real_roots, 1)}
        )
        steps.append(
            _solve_step(
                ", ".join(f"{solve_for} = {answer.exact}" for answer in answers)
                if answers
                else status,
                explanation,
                final_latex,
                "answer",
                rule="real_solution_set",
                values=answer_values,
            )
        )
        verification_parts = [
            (
                root,
                sp.simplify(expanded.subs(target, root)),
            )
            for root in real_roots
        ]
        if verification_parts:
            verification_expression = "; ".join(
                f"{solve_for} = {sp.sstr(root)} -> {sp.sstr(remainder)} = 0"
                for root, remainder in verification_parts
            )
            verification_latex = r";\quad ".join(
                rf"{sp.latex(target)}={sp.latex(root)} \Rightarrow {sp.latex(remainder)}=0"
                for root, remainder in verification_parts
            )
            verification_values = {
                sp.sstr(root): remainder for root, remainder in verification_parts
            }
        else:
            verification_expression = (
                f"discriminant = {sp.sstr(discriminant)} < 0"
                if discriminant is not None and discriminant.is_negative is True
                else status
            )
            verification_latex = final_latex
            verification_values = {"status": status}
        verification_explanation = (
            "Thay từng nghiệm vào phương trình chuẩn và rút gọn chính xác về 0."
            if verification_parts
            else "Kiểm tra chính xác điều kiện cho tập nghiệm thực."
        )
        steps.append(
            _solve_step(
                verification_expression,
                verification_explanation,
                verification_latex,
                "verification",
                rule="exact_substitution",
                values=verification_values,
            )
        )
    response = MathSolveResponse(
        original_equation=raw,
        canonical_equation=canonical_equation,
        variables=variables,
        solve_for=solve_for,
        degree=degree,
        classification=classification,
        status=status,
        answers=answers,
        cases=cases,
        steps=steps,
        verified=verified,
    )
    _validate_finite_payload(response.model_dump())
    return response


def _projected_polynomial_degree(expr: sp.Expr) -> int | None:
    """Ước lượng bậc đa thức mà không expand; None nghĩa là không phải đa thức."""
    if not expr.has(_X):
        return 0
    if expr == _X:
        return 1
    if isinstance(expr, sp.Add):
        degrees = [_projected_polynomial_degree(arg) for arg in expr.args]
        return None if any(degree is None for degree in degrees) else max(degrees)
    if isinstance(expr, sp.Mul):
        degrees = [_projected_polynomial_degree(arg) for arg in expr.args]
        return None if any(degree is None for degree in degrees) else sum(degrees)
    if isinstance(expr, sp.Pow) and expr.exp.is_Integer and int(expr.exp) >= 0:
        base_degree = _projected_polynomial_degree(expr.base)
        return None if base_degree is None else base_degree * int(expr.exp)
    return None


def _validate_expansion_budget(expr: sp.Expr) -> None:
    """Ước lượng tăng tổ hợp mà không gọi expand."""
    operations = 0

    def projected_terms(node: sp.Expr) -> int:
        nonlocal operations
        operations += 1
        if operations > _MAX_EXPANSION_OPERATIONS:
            raise MathEngineError("Biểu thức vượt operation budget.")
        if isinstance(node, sp.Add):
            terms = sum(projected_terms(arg) for arg in node.args)
        elif isinstance(node, sp.Mul):
            terms = 1
            for arg in node.args:
                terms *= projected_terms(arg)
                if terms > _MAX_EXPANSION_TERMS:
                    raise MathEngineError("Biểu thức có projected expansion quá lớn.")
        elif isinstance(node, sp.Pow) and node.exp.is_Integer and int(node.exp) > 0:
            terms = projected_terms(node.base) ** int(node.exp)
        else:
            # expand() descends into function arguments, so their internal
            # products need the same budget even though the function is one term.
            for arg in node.args:
                projected_terms(arg)
            terms = 1
        if terms > _MAX_EXPANSION_TERMS:
            raise MathEngineError("Biểu thức có projected expansion quá lớn.")
        return terms

    projected_terms(expr)


def normalize_expression(raw: str) -> str:
    """Chuẩn hóa biểu thức thô thành dạng SymPy (dạng srepr)."""
    text = _prepare_text(raw)
    names = _variable_names(text)
    symbols = {name: sp.Symbol(name, real=True) for name in names}
    if "x" in text and "x" not in names:
        symbols["x"] = _X
    _validate_input_tokens(text, set(symbols))
    expr = _parse_limited(text, symbols or None)
    return sp.srepr(expr)


def canonical_expression(raw: str) -> str:
    """Biểu thức canonical dễ đọc cho nội dung sư phạm."""
    analysis_input = _parse_analysis_input(raw)
    canonical = sp.sstr(sp.cancel(analysis_input.expression))
    if analysis_input.source_variable != "x":
        canonical = re.sub(r"\bx\b", analysis_input.source_variable, canonical)
    return canonical


def _sample_points(
    expr: sp.Expr,
    center: float,
    range_: float | None = None,
    excluded: set[float] | None = None,
) -> list[list[float]]:
    """Sinh điểm mẫu [x, y] quanh center để vẽ đồ thị (bỏ điểm không xác định)."""
    x = sp.Symbol("x")
    half = range_ if range_ is not None else _SAMPLE_RANGE
    points: list[list[float]] = []
    if not math.isfinite(center) or not math.isfinite(half) or half < 0:
        raise MathEngineError("Cửa sổ lấy mẫu phải hữu hạn.")
    for index in range(_SAMPLE_COUNT):
        t = center - half + (2 * half * index / (_SAMPLE_COUNT - 1))
        if excluded and any(abs(t - value) < 1e-9 for value in excluded):
            continue
        try:
            y = float(expr.subs(x, t))
        except (TypeError, ValueError):
            y = float("nan")
        if math.isfinite(y):
            points.append([round(float(t), 4), round(y, 4)])
    return points


def _finite_float(value: sp.Expr | float, label: str) -> float:
    """Đổi sang float và không cho phép NaN/Infinity đi vào features."""
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise MathEngineError(f"{label} phải là số hữu hạn.") from exc
    if not math.isfinite(result):
        raise MathEngineError(f"{label} phải là số hữu hạn.")
    if result == 0 and value != 0:
        raise MathEngineError(f"{label} quá nhỏ và bị underflow.")
    return result


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
            a = _finite_float(m[a_w], "Hệ số a")
            b = _finite_float(m[b_w], "Hệ số b")
            c = _finite_float(m[c_w], "Hệ số c")
            d = _finite_float(m.get(d_w, 0), "Hệ số d")
        except MathEngineError:
            continue
        if a != 0 and b != 0:
            return func, a, b, c, d
    return None


def _trig_roots(
    match: tuple[str, float, float, float, float], center: float, period: float
) -> list[float]:
    """Tìm nghiệm giải tích trong cửa sổ hai chu kỳ quanh center."""
    func, a, b, c, d = match
    lo = center - period
    hi = center + period
    boundary_tolerance = max(
        abs(period) * 1e-12,
        4 * max(math.ulp(lo), math.ulp(hi), math.ulp(center)),
    )
    target = _finite_float(-d / a, "Tỷ lệ nghiệm lượng giác")
    target_tolerance = max(
        4 * math.ulp(target),
        4 * (math.ulp(d) + abs(target) * math.ulp(a)) / abs(a),
    )
    if not math.isfinite(target_tolerance):
        raise MathEngineError("Tolerance nghiệm lượng giác phải hữu hạn.")
    if 1 < target <= 1 + target_tolerance:
        target = 1.0
    elif -1 - target_tolerance <= target < -1:
        target = -1.0
    elif target < -1 or target > 1:
        return []
    if func == "sin":
        principal = math.asin(target)
        theta_families = (principal, math.pi - principal)
    else:
        principal = math.acos(target)
        theta_families = (principal, -principal)
    roots = [
        (theta + 2 * math.pi * k - c) / b
        for theta in theta_families
        for k in range(-3, 4)
        if lo - boundary_tolerance
        <= (theta + 2 * math.pi * k - c) / b
        <= hi + boundary_tolerance
    ]
    deduped: list[float] = []
    for r in sorted(roots):
        tolerance = max(
            abs(period) * 1e-12,
            4 * max(math.ulp(r), math.ulp(deduped[-1]) if deduped else 0.0),
        )
        if not deduped or abs(r - deduped[-1]) > tolerance:
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
        (a_w * b_w ** (k_w * x) + c_w, "scaled_pow"),
        (a_w * b_w ** (k_w * x), "scaled_pow"),
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
            a = _finite_float(m[a_w], "Hệ số a")
            c = _finite_float(m.get(c_w, 0), "Hệ số c")
        except MathEngineError:
            continue
        if a == 0:
            continue
        if kind in {"pow", "scaled_pow"}:
            if b_w not in m:
                continue
            base = m[b_w]
            if base == sp.E:
                base = math.e
            else:
                try:
                    base = _finite_float(base, "Cơ số")
                except MathEngineError:
                    continue
            if base <= 0 or base == 1:
                continue
            exponent_scale = 1.0
            if kind == "scaled_pow":
                try:
                    exponent_scale = _finite_float(m[k_w], "Hệ số mũ")
                except (KeyError, MathEngineError):
                    continue
            log_effective_base = exponent_scale * math.log(base)
            if not math.isfinite(log_effective_base) or not (
                math.log(sys.float_info.min)
                <= log_effective_base
                <= math.log(sys.float_info.max)
            ):
                raise MathEngineError("Cơ số hiệu dụng vượt giới hạn hữu hạn.")
            try:
                effective_base = base**exponent_scale
            except (OverflowError, ValueError, ZeroDivisionError) as exc:
                raise MathEngineError("Cơ số hiệu dụng không hợp lệ.") from exc
            if effective_base == 0 or effective_base == 1:
                raise MathEngineError("Cơ số hiệu dụng phải dương và khác 1.")
            return "pow", a, effective_base, c
        try:
            k = _finite_float(m[k_w], "Hệ số mũ")
        except MathEngineError:
            continue
        if k == 0:
            continue
        try:
            base = math.exp(k)
        except OverflowError as exc:
            raise MathEngineError("Cơ số hàm mũ phải hữu hạn.") from exc
        if not math.isfinite(base) or base == 0 or base == 1:
            raise MathEngineError("Cơ số hàm mũ phải dương, hữu hạn và khác 1.")
        return "exp", a, base, c
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
        if has_base and b_w not in m:
            continue
        try:
            a = _finite_float(m[a_w], "Hệ số a")
            c = _finite_float(m.get(c_w, 0), "Hệ số c")
            base = _finite_float(m[b_w], "Cơ số") if has_base else math.e
        except MathEngineError:
            continue
        if a == 0 or base <= 0 or base == 1:
            continue
        log_root = (-c / a) * math.log(base)
        if not math.isfinite(log_root) or not (
            math.log(sys.float_info.min) <= log_root <= math.log(sys.float_info.max)
        ):
            raise MathEngineError("Nghiệm logarit vượt giới hạn hữu hạn.")
        root = math.exp(log_root)
        if not math.isfinite(root) or root <= 0:
            raise MathEngineError("Nghiệm logarit phải dương và hữu hạn.")
        return a, base, c, root
    return None


def _has_variable_exponent(expr: sp.Expr) -> bool:
    return any(
        isinstance(node, sp.Pow)
        and not node.base.has(_X)
        and node.exp.has(_X)
        for node in sp.preorder_traversal(expr)
    ) or expr.has(sp.exp)


def _original_denominator_factors(expr: sp.Expr) -> list[sp.Expr]:
    """Thu thập mọi mẫu chứa x từ cấu trúc gốc, kể cả trong tổng phân thức."""
    factors: list[sp.Expr] = []
    for node in sp.preorder_traversal(expr):
        if not isinstance(node, sp.Pow) or not node.base.has(_X) or not node.exp.is_number:
            continue
        exponent = _bounded_numeric_value(node.exp)
        if exponent < 0:
            factors.append(node.base)
    return factors


def _validate_original_rational_terms(expr: sp.Expr) -> None:
    """Kiểm tra từng term trước khi tổng/cancel có thể che bậc hoặc mẫu zero."""
    denominator_factors = _original_denominator_factors(expr)
    if any(sp.simplify(_exactify_floats(factor)) == 0 for factor in denominator_factors):
        raise MathEngineError("Mẫu số gốc không được đồng nhất bằng 0.")
    for term in sp.Add.make_args(expr):
        term_denominators = _original_denominator_factors(term)
        if not term_denominators:
            continue
        numerator, denominator = sp.fraction(term)
        numerator = _exactify_floats(numerator)
        denominator = _exactify_floats(denominator)
        if sp.simplify(denominator) == 0:
            raise MathEngineError("Mẫu số gốc không được đồng nhất bằng 0.")
        try:
            numerator_poly = sp.Poly(numerator, _X)
            denominator_poly = sp.Poly(denominator, _X)
        except sp.PolynomialError as exc:
            raise MathEngineError("Mỗi rational term phải có tử/mẫu đa thức.") from exc
        if numerator_poly.degree() > 1 or denominator_poly.degree() > 1:
            raise MathEngineError(
                "Mỗi rational term chỉ hỗ trợ tử/mẫu bậc nhất."
            )


def _exactify_floats(expr: sp.Expr) -> sp.Expr:
    """Đổi Float nhập từ decimal thành Rational để so sánh đại số chính xác."""
    replacements = {
        value: sp.Rational(str(value))
        for value in expr.atoms(sp.Float)
    }
    return expr.xreplace(replacements)


def _real_roots_exact(expressions: list[sp.Expr]) -> list[sp.Expr]:
    roots: list[sp.Expr] = []
    for expression in expressions:
        expression = _exactify_floats(expression)
        try:
            poly = sp.Poly(expression, _X)
        except sp.PolynomialError as exc:
            raise MathEngineError("Mẫu số phải là đa thức bậc nhất.") from exc
        if poly.degree() > 1:
            raise MathEngineError("Mẫu số bậc cao chưa được hỗ trợ.")
        for root in sp.solve(sp.Eq(expression, 0), _X):
            if root.is_real and all(sp.simplify(root - existing) != 0 for existing in roots):
                roots.append(root)
    return sorted(roots, key=lambda root: _finite_float(root, "Nghiệm"))


def _real_roots(expressions: list[sp.Expr], label: str) -> list[float]:
    return [_finite_float(root, label) for root in _real_roots_exact(expressions)]


def _analyze_rational(
    expr: sp.Expr,
    original_num: sp.Expr,
    original_den: sp.Expr,
    original_denominators: list[sp.Expr],
    raw: str,
    latex: str,
    normalized: str,
) -> MathAnalyzeResponse:
    """Phân tích hàm phân thức bậc nhất/bậc nhất (ax + b)/(cx + d)."""
    x = sp.Symbol("x")
    expr = _exactify_floats(expr)
    original_num = _exactify_floats(original_num)
    original_den = _exactify_floats(original_den)
    original_denominators = [
        _exactify_floats(denominator) for denominator in original_denominators
    ]
    num, den = sp.fraction(sp.cancel(expr))
    try:
        original_npoly = sp.Poly(original_num, x)
        original_dpoly = sp.Poly(original_den, x)
        npoly = sp.Poly(num, x)
        dpoly = sp.Poly(den, x)
    except sp.PolynomialError as exc:
        raise MathEngineError(
            f"Chỉ hỗ trợ hàm phân thức bậc nhất/bậc nhất (ax + b)/(cx + d): {raw!r}"
        ) from exc
    if original_npoly.degree() > 1 or original_dpoly.degree() > 1:
        raise MathEngineError(
            f"Chỉ hỗ trợ hàm phân thức bậc nhất/bậc nhất (ax + b)/(cx + d): {raw!r}"
        )
    n_coeffs = original_npoly.all_coeffs()
    d_coeffs = original_dpoly.all_coeffs()
    a = _finite_float(n_coeffs[0], "Hệ số a") if original_npoly.degree() == 1 else 0.0
    b = (
        _finite_float(n_coeffs[1], "Hệ số b")
        if original_npoly.degree() == 1
        else _finite_float(n_coeffs[0], "Hệ số b")
    )
    c = _finite_float(d_coeffs[0], "Hệ số c") if original_dpoly.degree() == 1 else 0.0
    d = (
        _finite_float(d_coeffs[1], "Hệ số d")
        if original_dpoly.degree() == 1
        else _finite_float(d_coeffs[0], "Hệ số d")
    )

    exact_poles = _real_roots_exact(original_denominators or [original_den])
    exact_asymptote_poles = _real_roots_exact([den])
    poles = [_finite_float(pole, "Điểm loại trừ") for pole in exact_poles]
    asymptote_poles = [
        _finite_float(pole, "Tiệm cận đứng") for pole in exact_asymptote_poles
    ]
    holes = [
        _finite_float(pole, "Điểm khuyết")
        for pole in exact_poles
        if all(sp.simplify(pole - asymptote) != 0 for asymptote in exact_asymptote_poles)
    ]
    vertical_asymptotes = [f"x = {p:g}" for p in asymptote_poles]
    horizontal_asymptote: str | None = None
    lim = sp.limit(expr, x, sp.oo)
    if lim.is_finite:
        horizontal_asymptote = f"y = {_finite_float(lim, 'Tiệm cận ngang'):g}"
    else:
        lim_neg = sp.limit(expr, x, -sp.oo)
        if lim_neg.is_finite:
            horizontal_asymptote = f"y = {_finite_float(lim_neg, 'Tiệm cận ngang'):g}"
    roots = [
        _finite_float(root, "Nghiệm")
        for root in sp.solve(sp.Eq(num, 0), x)
        if root.is_real
        and all(sp.simplify(root - pole) != 0 for pole in exact_poles)
    ]
    root = roots[0] if len(roots) == 1 else None
    y_intercept = (
        _finite_float(expr.subs(x, 0), "Giao điểm trục tung")
        if all(sp.simplify(pole) != 0 for pole in exact_poles)
        else None
    )
    domain = "x ≠ " + "; ".join(f"{p:g}" for p in poles) if poles else "R"
    center = 1.0 if any(abs(p) < 1e-9 for p in poles) else 0.0
    features = RationalFeatures(
        a=a,
        b=b,
        c=c,
        d=d,
        poles=poles,
        holes=holes,
        vertical_asymptotes=vertical_asymptotes,
        horizontal_asymptote=horizontal_asymptote,
        root=root,
        y_intercept=y_intercept,
        domain=domain,
        sample_points=_sample_points(expr, center, excluded=set(poles)),
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
    period = _finite_float(2 * sp.pi / abs(b), "Chu kỳ")
    phase_shift = -c / b
    if not math.isfinite(phase_shift):
        raise MathEngineError("Độ lệch pha phải hữu hạn.")
    if period > _MAX_TRIG_PERIOD:
        raise MathEngineError("Chu kỳ vượt giới hạn phân tích.")
    if abs(phase_shift) > _MAX_TRIG_PHASE:
        raise MathEngineError("Độ lệch pha vượt giới hạn phân tích.")
    window_resolution = max(
        math.ulp(phase_shift),
        math.ulp(phase_shift - period),
        math.ulp(phase_shift + period),
    )
    if period <= window_resolution:
        raise MathEngineError("Chu kỳ nhỏ hơn độ phân giải tại cửa sổ phân tích.")
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
        roots=_trig_roots(match, phase_shift, period),
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
        x_intercept = _finite_float(
            sp.log(-c / a) / sp.log(base), "Giao điểm trục hoành"
        )
    features = ExponentialFeatures(
        a=a,
        b=base,
        c=c,
        base=base,
        direction="up" if a * math.log(base) > 0 else "down",
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
    original_expr: sp.Expr,
    raw: str,
    latex: str,
    normalized: str,
) -> MathAnalyzeResponse:
    """Phân tích biểu thức không phải đa thức: phân thức, lượng giác, mũ, logarit."""
    x = sp.Symbol("x")
    trig = _match_trig(expr)
    if trig is not None:
        return _analyze_trig(expr, trig, raw, latex, normalized)
    exp_match = _match_exp(expr)
    if exp_match is not None:
        return _analyze_exp(expr, exp_match, raw, latex, normalized)
    log_match = _match_log(expr)
    if log_match is not None:
        return _analyze_log(expr, log_match, raw, latex, normalized)
    if expr.is_rational_function(x):
        return _analyze_structural_rational(
            expr, original_expr, raw, latex, normalized
        )
    raise MathEngineError(
        "Loại hàm chưa được hỗ trợ (MVP: bậc hai, bậc nhất, phân thức, "
        "lượng giác sin/cos, mũ, logarit)."
    )


def _analyze_structural_rational(
    expr: sp.Expr,
    original_expr: sp.Expr,
    raw: str,
    latex: str,
    normalized: str,
) -> MathAnalyzeResponse:
    """Route rational theo mẫu gốc mà không chạy wildcard match."""
    original_num, original_den = sp.fraction(original_expr)
    original_denominators = _original_denominator_factors(original_expr)
    if not original_den.has(_X):
        original_num, original_den = sp.fraction(sp.cancel(expr))
    return _analyze_rational(
        expr,
        original_num,
        original_den,
        original_denominators,
        raw,
        latex,
        normalized,
    )


def _analyze_expression(
    raw: str, analysis_input: _AnalysisInput | None = None
) -> MathAnalyzeResponse:
    """Phân tích biểu thức, ưu tiên hàm bậc hai (phạm vi MVP)."""
    x = sp.Symbol("x")
    analysis_input = analysis_input or _parse_analysis_input(raw)
    parsed = analysis_input.expression
    if _original_denominator_factors(parsed) and not _has_variable_exponent(parsed):
        _validate_original_rational_terms(parsed)
    projected_degree = _projected_polynomial_degree(parsed)
    if projected_degree is not None and projected_degree > 2:
        raise MathEngineError("Bậc đa thức dự kiến vượt phạm vi hỗ trợ.")
    _validate_expansion_budget(parsed)
    expr = sp.expand(parsed)
    latex = sp.latex(expr)
    normalized = sp.srepr(expr)

    if _original_denominator_factors(parsed):
        if _has_variable_exponent(expr):
            exp_match = _match_exp(expr)
            if exp_match is not None:
                return _analyze_exp(expr, exp_match, raw, latex, normalized)
        return _analyze_structural_rational(expr, parsed, raw, latex, normalized)

    try:
        poly = sp.Poly(expr, x)
    except sp.PolynomialError:
        return _analyze_non_polynomial(expr, parsed, raw, latex, normalized)
    degree = poly.degree()
    coeffs = poly.all_coeffs()

    if degree == 2:
        a, b, c = (
            _finite_float(coeffs[i], f"Hệ số {name}")
            for i, name in enumerate(("a", "b", "c"))
        )
        d = _finite_float(b * b - 4 * a * c, "Biệt thức")
        h = _finite_float(-b / (2 * a), "Hoành độ đỉnh")
        k = _finite_float(-d / (4 * a), "Tung độ đỉnh")
        roots = sorted(
            _finite_float(r, "Nghiệm")
            for r in sp.solve(sp.Eq(expr, 0), x)
            if r.is_real
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
        a, b = (
            _finite_float(coeffs[i], f"Hệ số {name}")
            for i, name in enumerate(("a", "b"))
        )
        root = _finite_float(-b / a, "Nghiệm") if a != 0 else None
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


def _validate_finite_payload(value: object, path: str = "response") -> None:
    """Không cho phép bất kỳ derived numeric fact NaN/Infinity vào response."""
    if isinstance(value, float):
        if not math.isfinite(value):
            raise MathEngineError(f"{path} phải hữu hạn.")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _validate_finite_payload(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_finite_payload(item, f"{path}[{index}]")


def analyze_expression(raw: str) -> MathAnalyzeResponse:
    """Phân tích rồi áp dụng finite gate tập trung trước khi trả response."""
    analysis_input = _parse_analysis_input(raw)
    response = _analyze_expression(raw, analysis_input)
    canonical = sp.sstr(sp.cancel(analysis_input.expression))
    if analysis_input.source_variable != "x":
        canonical = re.sub(r"\bx\b", analysis_input.source_variable, canonical)
    response.canonical_expression = canonical
    response.source_variable = analysis_input.source_variable
    response.dependent_variable = analysis_input.dependent_variable
    _validate_finite_payload(response.model_dump())
    return response
