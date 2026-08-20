"""Interface CopilotProvider - đề xuất nội dung sư phạm cho một Activity.

Lộ trình: RuleBased (mock) -> Ollama Chat (local LLM) -> Production.
Math Engine là nguồn sự thật; provider không được tự tính toán kết quả.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.copilot import CopilotRequest, CopilotSuggestion


class CopilotProvider(ABC):
    """Đề xuất nội dung giảng dạy dựa trên đặc trưng toán học đã xác nhận."""

    name: str = "base"

    @abstractmethod
    def suggest(self, request: CopilotRequest) -> CopilotSuggestion:
        """Tạo nội dung sư phạm (summary, key_points, questions, examples, steps).

        Kết quả là JSON có schema; giáo viên phải duyệt trước khi lên bảng.
        """
        raise NotImplementedError