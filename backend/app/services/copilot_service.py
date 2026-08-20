"""Dịch vụ Teacher Copilot - chọn provider theo cài đặt (xem copilot_settings)."""

from __future__ import annotations

from app.providers.copilot_base import CopilotProvider
from app.providers.ollama_copilot import OllamaCopilotProvider
from app.providers.rule_based_copilot import RuleBasedCopilotProvider
from app.schemas.copilot import CopilotRequest, CopilotSuggestion
from app.services.copilot_settings import (
    AVAILABLE_COPILOT_PROVIDERS,
    get_active_copilot_provider,
)


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