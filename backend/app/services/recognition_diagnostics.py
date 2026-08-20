"""Kiểm tra khả dụng của từng provider nhận dạng (Ollama Vision, Pix2Text...).

Chỉ ping dịch vụ ngoài khi được gọi (mở popover / nút "Kiểm tra lại"),
KHÔNG chạy trong poll định kỳ 10s của Toolbar.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import httpx

from app.services.recognition_settings import AVAILABLE_PROVIDERS

_DIAGNOSTIC_TIMEOUT = 1.5


@dataclass(frozen=True)
class ProviderAvailability:
    """Trạng thái khả dụng của một provider nhận dạng."""

    provider: str
    available: bool
    detail: str


def _ollama_url() -> str:
    return os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")


def _ollama_model() -> str:
    return os.environ.get("OLLAMA_MODEL", "llava")


def _pix2text_url() -> str:
    return os.environ.get("PIX2TEXT_URL", "http://localhost:8503").rstrip("/")


def _check_ollama_vision(client: httpx.Client) -> ProviderAvailability:
    url = _ollama_url()
    model = _ollama_model()
    try:
        response = client.get(f"{url}/api/tags")
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return ProviderAvailability(
            provider="ollama_vision",
            available=False,
            detail=(
                f"Chưa kết nối được Ollama ({url}). Cài tại ollama.com rồi chạy "
                f"'ollama serve' (chi tiết: {exc})"
            ),
        )
    models = [
        item.get("name", "") for item in (response.json().get("models") or [])
    ]
    if not any(model in name or name in model for name in models):
        return ProviderAvailability(
            provider="ollama_vision",
            available=True,
            detail=(
                f"Ollama đang chạy ({url}) nhưng chưa có model '{model}' — "
                f"chạy 'ollama pull {model}'"
            ),
        )
    return ProviderAvailability(
        provider="ollama_vision",
        available=True,
        detail=f"Ollama sẵn sàng (model '{model}' đã cài)",
    )


def _check_pix2text(client: httpx.Client) -> ProviderAvailability:
    url = _pix2text_url()
    try:
        response = client.get(f"{url}/")
    except httpx.HTTPError as exc:
        return ProviderAvailability(
            provider="pix2text",
            available=False,
            detail=(
                f"Chưa kết nối được Pix2Text ({url}). Cài bằng 'pip install "
                f"pix2text[serve]' rồi chạy 'p2t serve' (chi tiết: {exc})"
            ),
        )
    return ProviderAvailability(
        provider="pix2text",
        available=True,
        detail=f"Pix2Text sẵn sàng ({url})",
    )


def check_provider_availability(
    name: str,
    http_client: httpx.Client | None = None,
) -> ProviderAvailability:
    """Kiểm tra khả dụng của một provider; mock luôn sẵn sàng."""
    if name == "mock":
        return ProviderAvailability(
            provider="mock",
            available=True,
            detail="Giả lập, không cần kết nối",
        )
    client = http_client or httpx.Client(timeout=_DIAGNOSTIC_TIMEOUT)
    if name == "ollama_vision":
        return _check_ollama_vision(client)
    if name == "pix2text":
        return _check_pix2text(client)
    return ProviderAvailability(
        provider=name,
        available=False,
        detail=f"Provider không xác định: {name}",
    )


def check_all(http_client: httpx.Client | None = None) -> list[ProviderAvailability]:
    """Kiểm tra khả dụng của toàn bộ provider khả dụng (chạy song song)."""
    client = http_client or httpx.Client(timeout=_DIAGNOSTIC_TIMEOUT)
    with ThreadPoolExecutor(max_workers=len(AVAILABLE_PROVIDERS)) as pool:
        results = list(pool.map(lambda name: check_provider_availability(name, client), AVAILABLE_PROVIDERS))
    return results