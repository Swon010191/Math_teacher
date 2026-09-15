"""API Teacher Copilot - đề xuất nội dung sư phạm + quản lý provider."""

from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.schemas.copilot import CopilotRequest, CopilotSuggestion
from app.services.copilot_service import suggest
from app.services.copilot_settings import (
    AVAILABLE_COPILOT_PROVIDERS,
    get_active_copilot_provider,
    set_active_copilot_provider,
)
from app.services.math_service import MathEngineError

router = APIRouter(prefix="/api/copilot", tags=["copilot"])


class CopilotProviderState(BaseModel):
    """Trạng thái provider Copilot hiện tại."""

    provider: str
    available: list[str]


class SetCopilotProviderRequest(BaseModel):
    """Yêu cầu đổi provider Copilot."""

    provider: str


@router.post("/suggest", response_model=CopilotSuggestion)
def suggest_content(request: CopilotRequest) -> CopilotSuggestion:
    """Đề xuất nội dung giảng dạy dựa trên đặc trưng toán học (Math Engine).

    Kết quả chỉ là đề xuất - giáo viên phải duyệt trước khi đưa lên bảng.
    """
    try:
        return suggest(request)
    except MathEngineError as exc:
        raise HTTPException(
            status_code=400,
            detail="Biểu thức không hợp lệ hoặc không được hỗ trợ.",
        ) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - lỗi provider
        detail = re.sub(r"https?://[^\s),;]+", "<dịch vụ AI>", str(exc))
        raise HTTPException(status_code=500, detail=detail) from exc


@router.get("/provider", response_model=CopilotProviderState)
def get_copilot_provider_state() -> CopilotProviderState:
    """Provider Copilot đang dùng và danh sách khả dụng."""
    return CopilotProviderState(
        provider=get_active_copilot_provider(),
        available=list(AVAILABLE_COPILOT_PROVIDERS),
    )


@router.put("/provider", response_model=CopilotProviderState)
def change_copilot_provider(request: SetCopilotProviderRequest) -> CopilotProviderState:
    """Đổi provider Copilot trong lúc chạy (restart sẽ trở về .env)."""
    try:
        set_active_copilot_provider(request.provider)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CopilotProviderState(
        provider=get_active_copilot_provider(),
        available=list(AVAILABLE_COPILOT_PROVIDERS),
    )
