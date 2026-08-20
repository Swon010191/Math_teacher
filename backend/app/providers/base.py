"""Interface RecognitionProvider - cho phép thay thế implementation.

Lộ trình: Mock (Stage 1) -> Ollama Vision (LLaVA/Qwen-VL) -> Pix2Text -> Production.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.recognition import RecognizeResult


class RecognitionProvider(ABC):
    """Nhận dạng nét viết tay/vùng ảnh thành công thức."""

    name: str = "base"

    @abstractmethod
    def recognize(
        self,
        image_base64: str | None = None,
        hint: str | None = None,
    ) -> RecognizeResult:
        """Nhận dạng ảnh (base64) hoặc vùng được chọn thành công thức.

        Kết quả luôn đi kèm confidence; bước xác nhận của giáo viên là bắt buộc.
        """
        raise NotImplementedError