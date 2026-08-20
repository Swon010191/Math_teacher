"""Dịch vụ nhận dạng - chọn provider theo cài đặt hiện tại (xem recognition_settings)."""

from __future__ import annotations

from app.providers.base import RecognitionProvider
from app.providers.mock import MockRecognitionProvider
from app.providers.ollama_vision import OllamaVisionProvider
from app.providers.pix2text import Pix2TextProvider
from app.schemas.recognition import RecognizeResult
from app.services.recognition_settings import get_active_provider


def _build_provider() -> RecognitionProvider:
    name = get_active_provider()
    if name == "mock":
        return MockRecognitionProvider()
    if name == "ollama_vision":
        return OllamaVisionProvider()
    if name == "pix2text":
        return Pix2TextProvider()
    raise ValueError(f"Provider không hợp lệ: {name!r}")


def recognize(
    image_base64: str | None = None,
    hint: str | None = None,
) -> RecognizeResult:
    provider = _build_provider()
    try:
        return provider.recognize(image_base64=image_base64, hint=hint)
    except Exception as exc:  # noqa: BLE001 - báo rõ lỗi provider lên API
        raise RuntimeError(f"Lỗi nhận dạng ({provider.name}): {exc}") from exc