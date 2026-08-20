"""Dịch vụ nhận dạng - chọn provider theo cấu hình (RECOGNITION_PROVIDER)."""

from __future__ import annotations

import os

from app.providers.base import RecognitionProvider
from app.providers.mock import MockRecognitionProvider
from app.schemas.recognition import RecognizeResult


def _build_provider() -> RecognitionProvider:
    name = os.environ.get("RECOGNITION_PROVIDER", "mock").strip().lower()
    if name == "ollama_vision":
        # TODO (giai đoạn sau): OllamaVisionProvider với LLaVA/Qwen-VL
        raise NotImplementedError("OllamaVisionProvider chưa được triển khai.")
    if name == "pix2text":
        # TODO (giai đoạn sau): Pix2TextProvider cho Math OCR
        raise NotImplementedError("Pix2TextProvider chưa được triển khai.")
    return MockRecognitionProvider()


def recognize(
    image_base64: str | None = None,
    hint: str | None = None,
) -> RecognizeResult:
    provider = _build_provider()
    return provider.recognize(image_base64=image_base64, hint=hint)