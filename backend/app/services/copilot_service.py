"""Dịch vụ Teacher Copilot - chọn provider theo cấu hình (COPILOT_PROVIDER)."""

from __future__ import annotations

import os

from app.providers.copilot_base import CopilotProvider
from app.providers.ollama_copilot import OllamaCopilotProvider
from app.providers.rule_based_copilot import RuleBasedCopilotProvider
from app.schemas.copilot import CopilotRequest, CopilotSuggestion

AVAILABLE_COPILOT_PROVIDERS: tuple[str, ...] = ("rule_based", "ollama")


def get_active_copilot_provider() -> str:
    """Tên provider Copilot đang dùng (đọc từ môi trường)."""
    name = os.environ.get("COPILOT_PROVIDER", "rule_based").strip().lower()
    if name not in AVAILABLE_COPILOT_PROVIDERS:
        name = "rule_based"
    return name


def _build_provider() -> CopilotProvider:
    name = get_active_copilot_provider()
    if name == "ollama":
        return OllamaCopilotProvider()
    return RuleBasedCopilotProvider()


def suggest(request: CopilotRequest) -> CopilotSuggestion:
    """Đề xuất nội dung sư phạm cho Activity (giáo viên phải duyệt trước)."""
    provider = _build_provider()
    try:
        return provider.suggest(request)
    except Exception as exc:  # noqa: BLE001 - báo rõ lỗi provider lên API
        raise RuntimeError(f"Lỗi Copilot ({provider.name}): {exc}") from exc