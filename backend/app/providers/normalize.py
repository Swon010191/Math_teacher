"""Chuẩn hóa kết quả thô từ model nhận dạng thành biểu thức SymPy."""

from __future__ import annotations

import re


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
    # 3. Logarit ghi cơ số: \log_{10}(x), \lg_2(x) -> log(x, base).
    text = re.sub(
        r"\\(?:log|lg|ln)\s*_\s*\{?([^{}()]+)\}?\s*\(([^()]*)\)",
        lambda m: f"log({m.group(2)},{m.group(1)})",
        text,
    )
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


def to_expression(text: str) -> str:
    """Chuẩn hóa công thức thô từ model.

    - Bỏ vế trái (y = ..., f(x) = ...) nếu có.
    - Chuyển LaTeX (\\frac, \\sqrt, \\cdot...) thành cú pháp SymPy.
    """
    expr = text.strip()
    match = re.match(r"^(?:y|f\(x\))\s*=\s*(.+)$", expr, re.IGNORECASE)
    if match:
        expr = match.group(1)
    return _latex_to_sympy(expr)