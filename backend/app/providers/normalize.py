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


def _find_matching_brace(text: str, open_index: int) -> int:
    """Vị trí } tương ứng với { tại open_index (-1 nếu lẻ)."""
    depth = 0
    for i in range(open_index, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _extract_braced(text: str, start: int) -> tuple[str, int] | None:
    """Lấy nội dung trong {...} bắt đầu tại start (start phải là '{')."""
    if start >= len(text) or text[start] != "{":
        return None
    end = _find_matching_brace(text, start)
    if end == -1:
        return None
    return text[start + 1 : end], end


def _replace_frac_brace_aware(text: str) -> str:
    """Thay \\frac{a}{b} brace-aware (chịu lồng nhau) - lặp đến ổn định."""
    # Lặp ngoài để xử lý lồng nhau: mỗi vòng thay các \frac mà args không chứa \frac lồng
    # Dùng vòng lặp với extract để xử lý nested
    prev = None
    cur = text
    guard = 0
    while prev != cur and guard < 20:
        guard += 1
        prev = cur
        out = []
        i = 0
        replaced = False
        while i < len(cur):
            m = re.search(r"\\(?:frac|dfrac|tfrac|cfrac)\s*\{", cur[i:])
            if not m:
                out.append(cur[i:])
                break
            s = i + m.start()
            out.append(cur[i:s])
            brace_start = cur.find("{", s)
            first = _extract_braced(cur, brace_start)
            if first is None:
                out.append(cur[s:])
                break
            content_a, end_a = first
            j = end_a + 1
            while j < len(cur) and cur[j].isspace():
                j += 1
            if j >= len(cur) or cur[j] != "{":
                out.append(cur[s : end_a + 1])
                i = end_a + 1
                continue
            second = _extract_braced(cur, j)
            if second is None:
                out.append(cur[s : end_a + 1])
                i = end_a + 1
                continue
            content_b, end_b = second
            out.append(f"({content_a})/({content_b})")
            i = end_b + 1
            replaced = True
        cur = "".join(out)
        if not replaced:
            break
    return cur


def _replace_sqrt_brace_aware(text: str) -> str:
    """Xử \\sqrt[3]{x} và \\sqrt{x} brace-aware."""
    # \sqrt[n]{x}
    pattern = re.compile(r"\\sqrt\s*\[")
    out = []
    i = 0
    while i < len(text):
        m = pattern.search(text, i)
        if not m:
            break
        out.append(text[i : m.start()])
        # find closing ]
        close = text.find("]", m.end())
        if close == -1:
            out.append(text[m.start() :])
            i = len(text)
            break
        n_content = text[m.end() : close]
        j = close + 1
        while j < len(text) and text[j].isspace():
            j += 1
        if j >= len(text) or text[j] != "{":
            out.append(text[m.start() : j])
            i = j
            continue
        inner = _extract_braced(text, j)
        if inner is None:
            out.append(text[m.start() : j + 1])
            i = j + 1
            continue
        content, end = inner
        out.append(f"{content}**(1/({n_content}))")
        i = end + 1
        # append tail later; rebuild and re-scan? simpler continue loop
        text = "".join(out) + text[i:]
        out = []
        i = 0
        # restart scan for remaining
        continue
    # simple \sqrt{...}
    # Use iterative brace-aware for \sqrt{ }
    result = "".join(out) + text[i:] if out else text
    # now handle \sqrt{ }
    out2 = []
    i = 0
    while i < len(result):
        m = re.search(r"\\sqrt\s*\{", result[i:])
        if not m:
            out2.append(result[i:])
            break
        s = i + m.start()
        out2.append(result[i:s])
        brace_start = result.find("{", s)
        inner = _extract_braced(result, brace_start)
        if inner is None:
            out2.append(result[s:])
            break
        content, end = inner
        out2.append(f"sqrt({content})")
        i = end + 1
    return "".join(out2)


def _replace_calculus_latex(text: str) -> str:
    """Chuyển \\int, \\sum, \\prod, \\lim, \\infty, \\Gamma, ma trận sang SymPy."""
    # \infty -> oo
    text = text.replace(r"\infty", "oo").replace(r"\infin", "oo")
    # \Gamma, \Gamma( -> gamma
    text = re.sub(r"\\Gamma\b", "gamma", text)
    text = re.sub(r"\\operatorname\{gamma\}", "gamma", text)
    text = re.sub(r"\\operatorname\{erf\}", "erf", text)
    # \int_{a}^{b} f dx  -> Integral(f, (x, a, b))  — heuristic
    # Dạng đơn giản: \int_{a}^{b} hoặc \int_a^b
    # Xử lý có brace
    def _int_repl(m: re.Match[str]) -> str:
        lower = m.group(1) or m.group(2) or ""
        upper = m.group(3) or m.group(4) or ""
        # lower dạng x= a hoặc a ; upper dạng b
        # Để đơn giản, nếu lower chứa '=', tách biến
        lower = lower.strip("{} ")
        upper = upper.strip("{} ")
        # Heuristic: sẽ được hậu xử lý thành Integral placeholder, normalize sẽ giữ nguyên để parser xử (SymPy parse Integral)
        # Tạm thay bằng Integral( ... ) wrapper — phần integrand sẽ ở sau
        # Dùng marker để _latex_to_sympy tiếp tục xử phần sau
        if lower and upper:
            return f"Integral(_INTEGRAND_, ({lower},{upper}))".replace("_INTEGRAND_", "PLACEHOLDER")
        if lower:
            return f"Integral(PLACEHOLDER, ({lower}))"
        return "Integral(PLACEHOLDER, x)"

    # Thử thay \int_{...}^{...} và \int^{...}_{...}
    text = re.sub(r"\\int\s*_\{([^{}]*)\}\s*\^\{([^{}]*)\}", lambda m: f"Integral(PLACEHOLDER, ({m.group(1)}, {m.group(2)}))", text)
    text = re.sub(r"\\int\s*\^\{([^{}]*)\}\s*_\{([^{}]*)\}", lambda m: f"Integral(PLACEHOLDER, ({m.group(2)}, {m.group(1)}))", text)
    text = re.sub(r"\\int\s*_\{([^{}]*)\}", lambda m: f"Integral(PLACEHOLDER, ({m.group(1)}))", text)
    text = re.sub(r"\\int\b", "Integral", text)
    # \sum_{i=1}^{n}  -> Sum(PLACEHOLDER, (i,1,n))
    text = re.sub(r"\\sum\s*_\{([^{}]*)\}\s*\^\{([^{}]*)\}", lambda m: f"Sum(PLACEHOLDER, ({m.group(1)}, {m.group(2)}))", text)
    text = re.sub(r"\\prod\s*_\{([^{}]*)\}\s*\^\{([^{}]*)\}", lambda m: f"Product(PLACEHOLDER, ({m.group(1)}, {m.group(2)}))", text)
    # \lim_{x \to a} -> Limit(PLACEHOLDER, x, a)
    text = re.sub(r"\\lim\s*_\{([^{}]*)\}", lambda m: f"Limit(PLACEHOLDER, {m.group(1)})", text)
    text = text.replace("PLACEHOLDER", "1")  # fallback nếu không có integrand rõ; SymPy sẽ parse được để không crash, analyzer sẽ bỏ placeholder
    # Ma trận \begin{matrix}...\end{matrix} -> Matrix([[..]])
    def _matrix_repl(m: re.Match[str]) -> str:
        inner = m.group(1)
        # inner dạng a & b \\ c & d
        rows = re.split(r"\\\\", inner)
        py_rows = []
        for r in rows:
            cols = [c.strip() for c in r.split("&") if c.strip() != ""]
            if cols:
                py_rows.append("[" + ",".join(cols) + "]")
        return "Matrix([[" + "],[".join(c.strip("[]") for c in py_rows) + "]])" if py_rows else "Matrix([[0]])"

    text = re.sub(r"\\begin\{(?:matrix|pmatrix|bmatrix)\}(.*?)\\end\{(?:matrix|pmatrix|bmatrix)\}", _matrix_repl, text, flags=re.DOTALL)
    return text


def _latex_to_sympy(text: str) -> str:
    """Chuyển LaTeX thô (frac, sqrt, cdot, log_{10}...) sang cú pháp SymPy."""
    # 1. Phân số \frac{n}{d} brace-aware
    text = _replace_frac_brace_aware(text)
    # 2. Căn bậc n brace-aware
    text = _replace_sqrt_brace_aware(text)
    # 3. Calculus: \int, \sum, \lim, \infty, \Gamma, matrix
    text = _replace_calculus_latex(text)
    # 4. Logarit ghi cơ số: \log_{10}(...), \lg_2(...) -> log(..., base).
    text = _replace_latex_log_base(text)
    # 5. Ký hiệu phép toán và nhóm.
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
    # 6. Số mũ có ngoặc nhọn x^{2} -> x**(2); ngoặc nhọn còn lại -> ngoặc tròn.
    while True:
        new = re.sub(r"\^\{([^{}]*)\}", lambda m: f"**({m.group(1)})", text)
        if new == text:
            break
        text = new
    text = text.replace("{", "(").replace("}", ")")
    text = text.replace("^", "**")
    # 7. Bỏ dấu \ trước tên hàm còn sót (\sin -> sin, \ln -> ln...).
    text = re.sub(r"\\([A-Za-z]+)", r"\1", text)
    # 8. Gộp khoảng trắng thừa.
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
