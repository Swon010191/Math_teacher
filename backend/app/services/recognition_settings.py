"""Cài đặt Recognition - chọn provider đang dùng.

Provider có thể được đổi trong lúc chạy qua API (GET/PUT /api/recognize/provider);
khởi động lại backend sẽ trở về giá trị trong môi trường RECOGNITION_PROVIDER.
"""

from __future__ import annotations

import os
import threading

AVAILABLE_PROVIDERS: tuple[str, ...] = ("mock", "ollama_vision", "pix2text")


def _env_default() -> str:
    name = os.environ.get("RECOGNITION_PROVIDER", "mock").strip().lower()
    if name not in AVAILABLE_PROVIDERS:
        name = "mock"
    return name


_lock = threading.Lock()
_current: str = _env_default()


def get_active_provider() -> str:
    """Tên provider đang dùng (ưu tiên lựa chọn trong lúc chạy)."""
    with _lock:
        return _current


def set_active_provider(name: str) -> str:
    """Đổi provider trong lúc chạy; trả về tên đã đặt."""
    normalized = name.strip().lower()
    if normalized not in AVAILABLE_PROVIDERS:
        raise ValueError(
            f"Provider không hợp lệ: {name!r} (cho phép: {', '.join(AVAILABLE_PROVIDERS)})"
        )
    with _lock:
        globals()["_current"] = normalized
    return normalized