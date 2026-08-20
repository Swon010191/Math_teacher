"""MockRecognitionProvider - dùng để hoàn thiện UI và luồng xử lý trước.

Trả về một công thức mẫu có kiểm soát để demo luồng:
vẽ -> chọn vùng -> nhận dạng -> xác nhận/sửa -> phân tích -> activity.
"""

from __future__ import annotations

import time

from app.providers.base import RecognitionProvider
from app.schemas.recognition import RecognizeResult

_SAMPLES: list[tuple[str, str, float]] = [
    ("y = x^2 - 4x + 3", "x**2 - 4*x + 3", 0.94),
    ("y = 2x^2 + 3x - 2", "2*x**2 + 3*x - 2", 0.88),
    ("y = -x^2 + 6x - 5", "-x**2 + 6*x - 5", 0.91),
]


class MockRecognitionProvider(RecognitionProvider):
    """Provider giả lập: luân phiên trả về các công thức mẫu."""

    name = "mock"

    def __init__(self, delay_seconds: float = 0.8) -> None:
        self._delay = delay_seconds
        self._index = 0

    def recognize(
        self,
        image_base64: str | None = None,
        hint: str | None = None,
    ) -> RecognizeResult:
        time.sleep(self._delay)  # Mô phỏng độ trễ của model thật
        latex, expression, confidence = _SAMPLES[self._index % len(_SAMPLES)]
        self._index += 1
        return RecognizeResult(
            latex=latex,
            expression=expression,
            confidence=confidence,
            provider=self.name,
            raw=None,
        )