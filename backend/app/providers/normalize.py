"""Chuẩn hóa kết quả thô từ model nhận dạng thành biểu thức SymPy."""

from __future__ import annotations

import re


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


def _replace_latex_log_base(text: str) -> str:
    """\\log_{10}(...) / \\lg_2(...) -> log(..., base), chịu ngoặc lồng."""
    pattern = re.compile(r"\\(?:log|lg|ln)\s*_\s*(\{([^{}]*)\}|([A-Za-z0-9]+))?\s*\(")
    while True:
        match = pattern.search(text)
        if not match:
            break
        base = match.group(2) if match.group(2) is not None else (match.group(3) or "")
        open_index = match.end() - 1
        close_index = _find_matching_paren(text, open_index)
        if close_index == -1:
            break
        inner = text[open_index + 1 : close_index]
        if not base:
            replacement = f"log({inner})"
        else:
            replacement = f"log({inner},{base})"
        text = text[: match.start()] + replacement + text[close_index + 1 :]
    return text


def _latex_to_sympy(text: str) -> str:
    """Chuyển LaTeX thô (frac, sqrt, cdot, log_{10}...) sang cú pháp SymPy."""
    # 1. Phân số \frac{n}{d} (kể cả \dfrac, \tfrac) - lặp cho phân số lồng nhau.
    frac_re = re.compile(r"\\(?:frac|dfrac|tfrac|cfrac)\s*\{([^{}]*)\}\s*\{([^{}]*)\}")
    while True:
        new = frac_re.sub(lambda m: f"({m.group(1)})/({m.group(2)})", text)
        if new == text:
            break
        text = new
    # 2. Căn bậc n: \sqrt[3]{x} -> x**(1/(3)); \sqrt{x} -> sqrt(x).
    text = re.sub(
        r"\\sqrt\s*\[([^{}]+)\]\s*\{([^{}]*)\}",
        lambda m: f"{m.group(2)}**(1/({m.group(1)}))",
        text,
    )
    text = re.sub(r"\\sqrt\s*\{([^{}]*)\}", lambda m: f"sqrt({m.group(1)})", text)
    # 3. Logarit ghi cơ số: \log_{10}(...), \lg_2(...) -> log(..., base).
    # Dùng quét ngoặc cân bằng để chịu được biểu thức lồng nhau.
    text = _replace_latex_log_base(text)
    # 4. Ký hiệu phép toán và nhóm.
    for cmd, repl in (
        (r"\cdot", "*"),
        (r"\times", "*"),
        (r"\ast", "*"),
        (r"\div", "/"),
        (r"\pi", "pi"),
    ):
        text = text.replace(cmd, repl)
    text = re.sub(r"\\text\s*\{([^{}]*)\}", lambda m: m.group(1), text)
    text = re.sub(r"\\(?:left|right)", "", text)
    text = re.sub(r"\\(?:,|;|:|!|quad|qquad)", " ", text)
    # 5. Số mũ có ngoặc nhọn x^{2} -> x**(2); ngoặc nhọn còn lại -> ngoặc tròn.
    while True:
        new = re.sub(r"\^\{([^{}]*)\}", lambda m: f"**({m.group(1)})", text)
        if new == text:
            break
        text = new
    text = text.replace("{", "(").replace("}", ")")
    text = text.replace("^", "**")
    # 6. Bỏ dấu \ trước tên hàm còn sót (\sin -> sin, \ln -> ln...).
    text = re.sub(r"\\([A-Za-z]+)", r"\1", text)
    # 7. Gộp khoảng trắng thừa.
    return re.sub(r"\s+", " ", text).strip()


def _strip_function_prefix(expr: str) -> str:
    """Bỏ vế trái định nghĩa hàm (y = ..., z = ..., f(x) = ..., g(t) = ...)."""
    identifier = r"[A-Za-z][A-Za-z0-9]*"
    match = re.match(
        rf"^(?:{identifier}|{identifier}\(\s*{identifier}\s*\))\s*=\s*(.+)$",
        expr,
        re.IGNORECASE,
    )
    if match:
        return match.group(1)
    return expr


def to_expression(text: str) -> str:
    """Chuẩn hóa công thức thô từ model.

    - Bỏ vế trái định nghĩa hàm (y = ..., z = ..., f(x) = ...) nếu có.
    - Chuyển LaTeX (\\frac, \\sqrt, \\cdot...) thành cú pháp SymPy.
    """
    return _latex_to_sympy(_strip_function_prefix(text.strip()))


def to_problem_expression(text: str) -> str:
    """Chuẩn hóa công thức/phương trình nhưng bảo toàn vế trái và dấu bằng."""
    prepared = re.sub(
        r"\^\{([^{}]*)\}", lambda match: f"**({match.group(1)})", text.strip()
    )
    expression = _latex_to_sympy(prepared)
    for glyph, replacement in (
        ("·", "*"),
        ("×", "*"),
        ("∗", "*"),
        ("∙", "*"),
        ("÷", "/"),
    ):
        expression = expression.replace(glyph, replacement)
    superscripts = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
    expression = re.sub(
        r"([⁰¹²³⁴⁵⁶⁷⁸⁹]+)",
        lambda match: "**" + match.group(1).translate(superscripts),
        expression,
    )
    return expression
