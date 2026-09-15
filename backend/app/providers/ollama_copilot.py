"""OllamaCopilotProvider - gọi LLM local (Ollama) để viết nội dung sư phạm.

System prompt yêu cầu model CHỈ dùng số liệu do Math Engine cung cấp
(nguồn sự thật), không tự tính toán, và trả về JSON đúng schema.
"""

from __future__ import annotations

import json
import os

import httpx
from pydantic import ValidationError

from app.providers.copilot_base import CopilotProvider
from app.schemas.copilot import CopilotRequest, CopilotSuggestion

_SYSTEM_PROMPT = (
    "Bạn là Teacher Copilot, trợ lý sư phạm cho giáo viên Toán (cấp THCS). "
    "Các số liệu toán học dưới đây đã được hệ thống máy tính (SymPy) tính chính xác - "
    "KHÔNG được tự tính toán lại, KHÔNG được thêm số liệu khác. Chỉ dùng các số liệu này "
    "để viết nội dung giảng dạy bằng tiếng Việt. Luôn dùng source_variable và "
    "dependent_variable đã cung cấp làm tên biến trong mọi công thức; không tự đổi về x/y. "
    "Trả về STRICT JSON không kèm văn bản thừa, đúng schema sau:\n"
    '{"summary": string, "key_points": string[], "questions": string[], '
    '"examples": [{"prompt": string, "solution": string}], '
    '"teaching_steps": string[], "confidence": number 0..1}'
)


class OllamaCopilotProvider(CopilotProvider):
    """Provider dùng LLM local qua Ollama /api/chat."""

    name = "ollama"

    def __init__(
        self,
        url: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 90.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._url = (url or os.environ.get("OLLAMA_URL", "http://localhost:11434")).rstrip("/")
        self._model = model or os.environ.get("OLLAMA_MODEL_COPILOT", "llama3.2")
        self._client = http_client or httpx.Client(timeout=timeout_seconds)

    def suggest(self, request: CopilotRequest) -> CopilotSuggestion:
        facts = request.math.model_dump(exclude_none=True)
        user_prompt = (
            f"Hoạt động: {request.activity_type}, cấp học: {request.grade_level}. "
            f"Biểu thức: {request.expression}. "
            f"Các số liệu đã tính sẵn (CHỈ dùng những số liệu này): {json.dumps(facts, ensure_ascii=False)}. "
            "Hãy đề xuất nội dung giảng dạy."
        )
        try:
            response = self._client.post(
                f"{self._url}/api/chat",
                json={
                    "model": self._model,
                    "stream": False,
                    "format": "json",
                    "messages": [
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                },
            )
            response.raise_for_status()
            payload = response.json()
            raw = payload.get("message", {}).get("content", "")
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Không kết nối được Ollama ({self._url}). "
                f"Kiểm tra: ollama serve đang chạy và đã pull model {self._model}. Chi tiết: {exc}"
            ) from exc

        if not raw:
            raise RuntimeError("Ollama trả về nội dung rỗng.")
        try:
            data = json.loads(raw)
            suggestion = CopilotSuggestion.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise RuntimeError(f"Ollama trả về JSON không đúng schema: {exc}") from exc
        return suggestion.model_copy(update={"provider": self.name})
