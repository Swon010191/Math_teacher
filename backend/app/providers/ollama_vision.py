"""OllamaVisionProvider - nhận dạng vùng ảnh bằng model vision local (LLaVA/Qwen-VL).

Cấu hình qua biến môi trường:
- RECOGNITION_PROVIDER=ollama_vision
- OLLAMA_URL (mặc định http://localhost:11434)
- OLLAMA_MODEL (mặc định llava)
"""

from __future__ import annotations

import base64
import json
import os

import httpx

from app.providers.base import RecognitionProvider
from app.providers.normalize import to_expression
from app.schemas.recognition import RecognizeResult

_PROMPT = """Bạn là công cụ nhận dạng công thức toán học từ ảnh chụp bảng.
Chỉ trả về MỘT đối tượng JSON hợp lệ với đúng 3 trường:
- "latex": công thức dạng LaTeX, ví dụ "y = x^2 - 4x + 3"
- "expression": biểu thức dạng SymPy (chỉ vế phải), ví dụ "x**2 - 4*x + 3"
- "confidence": số thực từ 0 đến 1 thể hiện độ tin cậy của bạn
Không thêm bất kỳ văn bản nào khác ngoài JSON."""


def _strip_data_url(image_base64: str | None) -> str:
    if not image_base64:
        raise ValueError("Thiếu ảnh vùng cần nhận dạng.")
    if image_base64.startswith("data:"):
        return image_base64.split(",", 1)[1]
    return image_base64


class OllamaVisionProvider(RecognitionProvider):
    """Nhận dạng bằng model vision chạy local qua Ollama."""

    name = "ollama_vision"

    def __init__(
        self,
        url: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 60.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._url = (url or os.environ.get("OLLAMA_URL", "http://localhost:11434")).rstrip("/")
        self._model = model or os.environ.get("OLLAMA_MODEL", "llava")
        self._client = http_client or httpx.Client(timeout=timeout_seconds)

    def recognize(
        self,
        image_base64: str | None = None,
        hint: str | None = None,
    ) -> RecognizeResult:
        image = _strip_data_url(image_base64)
        try:
            response = self._client.post(
                f"{self._url}/api/generate",
                json={
                    "model": self._model,
                    "prompt": _PROMPT,
                    "images": [image],
                    "stream": False,
                    "format": "json",
                },
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Không kết nối được Ollama ({self._url}, model {self._model}). "
                f"Kiểm tra: ollama serve đang chạy và đã cài model. Chi tiết: {exc}"
            ) from exc

        raw = payload.get("response", "")
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as exc:
            raise RuntimeError(
                f"Ollama không trả về JSON hợp lệ (model {self._model}): {raw[:300]!r}"
            ) from exc

        latex = str(data.get("latex", "")).strip()
        expression = to_expression(str(data.get("expression", latex)))
        confidence = float(data.get("confidence", 0.7))
        if not latex or not expression:
            raise RuntimeError(f"Ollama trả về công thức rỗng (model {self._model}).")
        return RecognizeResult(
            latex=latex,
            expression=expression,
            confidence=min(1.0, max(0.0, confidence)),
            provider=self.name,
            raw=raw,
        )