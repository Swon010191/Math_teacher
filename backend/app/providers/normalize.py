"""Chuẩn hóa kết quả thô từ model nhận dạng thành biểu thức SymPy."""

from __future__ import annotations

import re


def to_expression(text: str) -> str:
    """Chuẩn hóa công thức thô từ model.

    - Bỏ vế trái (y = ..., f(x) = ...) nếu có.
    - Chuyển ^ thành **, bỏ khoảng trắng thừa.
    """
    expr = text.strip()
    match = re.match(r"^(?:y|f\(x\))\s*=\s*(.+)$", expr, re.IGNORECASE)
    if match:
        expr = match.group(1)
    return expr.replace("^", "**").strip()