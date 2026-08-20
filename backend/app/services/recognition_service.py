"""Dịch vụ nhận dạng - chọn provider theo cấu hình (RECOGNITION_PROVIDER)."""

from __future__ import annotations

import os

from app.providers.base import RecognitionProvider
from app.providers.mock import MockRecognitionProvider
from app.providers.ollama_vision import OllamaVisionProvider
from app.providers.pix2text import Pix2TextProvider
from app.schemas.recognition import RecognizeResult


def _build_provider() -> RecognitionProvider:
    name = os.environ.get("RECOGNITION_PROVIDER", "mock").strip().lower()
    if name == "mock":
        return MockRecognitionProvider()
    if name == "ollama_vision":
        return OllamaVisionProvider(
            url=os.environ.get("OLLAMA_URL", "http://localhost:11434"),
            model=os.environ.get("OLLAMA_MODEL", "llava"),
        )
    if name == "pix2text":
        return Pix2TextProvider(url=os.environ.get("PIX2TEXT_URL", "http://localhost:8503"))
    raise ValueError(
        f"RECOGNITION_PROVIDER không hợp lệ: {name!r} (cho phép: mock, ollama_vision, pix2text)"
    )


def recognize(
    image_base64: str | None = None,
    hint: str | None = None,
) -> RecognizeResult:
    provider = _build_provider()
    try:
        return provider.recognize(image_base64=image_base64, hint=hint)
    except Exception as exc:  # noqa: BLE001 - báo rõ lỗi provider lên API
        raise RuntimeError(f"Lỗi nhận dạng ({provider.name}): {exc}") from exc