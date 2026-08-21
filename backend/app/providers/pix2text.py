"""Pix2TextProvider - Math OCR chuyên dụng cho công thức toán.

Chạy máy chủ Pix2Text local (p2t serve) rồi cấu hình:
- RECOGNITION_PROVIDER=pix2text
- PIX2TEXT_URL (mặc định http://localhost:8503)
"""

from __future__ import annotations

import base64
import os

import httpx

from app.providers.base import RecognitionProvider
from app.providers.normalize import to_problem_expression
from app.schemas.recognition import RecognizeResult


def _decode_image(image_base64: str | None) -> bytes:
    if not image_base64:
        raise ValueError("Thiếu ảnh vùng cần nhận dạng.")
    if image_base64.startswith("data:"):
        image_base64 = image_base64.split(",", 1)[1]
    return base64.b64decode(image_base64)


class Pix2TextProvider(RecognitionProvider):
    """Nhận dạng công thức toán (Math OCR) bằng Pix2Text."""

    name = "pix2text"

    def __init__(
        self,
        url: str | None = None,
        timeout_seconds: float = 60.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._url = (url or os.environ.get("PIX2TEXT_URL", "http://localhost:8503")).rstrip("/")
        self._client = http_client or httpx.Client(timeout=timeout_seconds)

    def recognize(
        self,
        image_base64: str | None = None,
        hint: str | None = None,
    ) -> RecognizeResult:
        try:
            image_bytes = _decode_image(image_base64)
        except (ValueError, base64.binascii.Error) as exc:
            raise ValueError(f"Ảnh nhận dạng không hợp lệ: {exc}") from exc

        try:
            response = self._client.post(
                f"{self._url}/pix2text",
                files={"image": ("region.png", image_bytes, "image/png")},
                data={"file_type": "formula", "resized_shape": "768"},
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Không kết nối được Pix2Text ({self._url}). "
                "Kiểm tra: p2t serve đang chạy. Chi tiết: {exc}"
            ) from exc

        results = payload.get("results") or []
        if isinstance(results, str):
            raw_text = results.strip()
        else:
            if not results:
                raise RuntimeError("Pix2Text không nhận dạng được nội dung nào trong vùng.")
            raw_text = str(results[0].get("text", "")).strip()
        if not raw_text:
            raise RuntimeError("Pix2Text trả về công thức rỗng.")
        latex = raw_text
        expression = to_problem_expression(raw_text)
        return RecognizeResult(
            latex=latex,
            expression=expression,
            confidence=0.9,
            provider=self.name,
            raw=raw_text,
        )
