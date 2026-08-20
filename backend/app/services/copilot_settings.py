"""Cài đặt Teacher Copilot - chọn provider đang dùng.

Provider có thể được đổi trong lúc chạy qua API (GET/PUT /api/copilot/provider);
khởi động lại backend sẽ trở về giá trị trong môi trường COPILOT_PROVIDER.
"""

from __future__ import annotations

import os
import threading

AVAILABLE_COPILOT_PROVIDERS: tuple[str, ...] = ("rule_based", "ollama")


def _env_default() -> str:
    name = os.environ.get("COPILOT_PROVIDER", "rule_based").strip().lower()
    if name not in AVAILABLE_COPILOT_PROVIDERS:
        name = "rule_based"
    return name


_lock = threading.Lock()
_current: str = _env_default()


def get_active_copilot_provider() -> str:
    """Tên provider Copilot đang dùng (ưu tiên lựa chọn trong lúc chạy)."""
    with _lock:
        return _current


def set_active_copilot_provider(name: str) -> str:
    """Đổi provider Copilot trong lúc chạy; trả về tên đã đặt."""
    normalized = name.strip().lower()
    if normalized not in AVAILABLE_COPILOT_PROVIDERS:
        raise ValueError(
            f"Provider không hợp lệ: {name!r} "
            f"(cho phép: {', '.join(AVAILABLE_COPILOT_PROVIDERS)})"
        )
    with _lock:
        globals()["_current"] = normalized
    return normalized