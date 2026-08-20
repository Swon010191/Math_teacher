"""API Teacher Copilot - đề xuất nội dung sư phạm cho Activity đã xác nhận."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.copilot import CopilotRequest, CopilotSuggestion
from app.services.copilot_service import suggest

router = APIRouter(prefix="/api/copilot", tags=["copilot"])


@router.post("/suggest", response_model=CopilotSuggestion)
def suggest_content(request: CopilotRequest) -> CopilotSuggestion:
    """Đề xuất nội dung giảng dạy dựa trên đặc trưng toán học (Math Engine).

    Kết quả chỉ là đề xuất - giáo viên phải duyệt trước khi đưa lên bảng.
    """
    try:
        return suggest(request)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - lỗi provider
        raise HTTPException(status_code=500, detail=str(exc)) from exc