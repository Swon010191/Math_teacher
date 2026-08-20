"""API Recognition - nhận dạng nét viết tay/vùng ảnh + quản lý provider."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.schemas.recognition import RecognizeRequest, RecognizeResult
from app.services.recognition_diagnostics import ProviderAvailability, check_all
from app.services.recognition_service import recognize
from app.services.recognition_settings import (
    AVAILABLE_PROVIDERS,
    get_active_provider,
    set_active_provider,
)

router = APIRouter(prefix="/api/recognize", tags=["recognition"])


class ProviderState(BaseModel):
    """Trạng thái provider nhận dạng hiện tại."""

    provider: str
    available: list[str]


class SetProviderRequest(BaseModel):
    """Yêu cầu đổi provider nhận dạng."""

    provider: str


@router.post("", response_model=RecognizeResult)
def recognize_expression(request: RecognizeRequest) -> RecognizeResult:
    """Nhận dạng vùng được chọn thành công thức toán học.

    Kết quả luôn có confidence; giáo viên phải xác nhận/sửa trước khi phân tích.
    """
    try:
        return recognize(image_base64=request.image_base64, hint=request.hint)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - lỗi provider
        raise HTTPException(status_code=500, detail=f"Lỗi nhận dạng: {exc}") from exc


@router.get("/provider", response_model=ProviderState)
def get_provider_state() -> ProviderState:
    """Provider nhận dạng đang dùng và danh sách khả dụng."""
    return ProviderState(
        provider=get_active_provider(),
        available=list(AVAILABLE_PROVIDERS),
    )


@router.put("/provider", response_model=ProviderState)
def change_provider(request: SetProviderRequest) -> ProviderState:
    """Đổi provider nhận dạng trong lúc chạy (restart sẽ trở về .env)."""
    try:
        set_active_provider(request.provider)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ProviderState(
        provider=get_active_provider(),
        available=list(AVAILABLE_PROVIDERS),
    )


class ProviderStatus(BaseModel):
    """Kết quả kiểm tra khả dụng của một provider nhận dạng."""

    provider: str
    available: bool
    detail: str


@router.get("/providers/status", response_model=list[ProviderStatus])
def get_providers_status() -> list[ProviderStatus]:
    """Trạng thái khả dụng của từng provider (ping dịch vụ ngoài).

    Chỉ gọi khi mở popover / bấm "Kiểm tra lại" - không dùng trong poll định kỳ.
    """
    return [
        ProviderStatus(
            provider=item.provider,
            available=item.available,
            detail=item.detail,
        )
        for item in check_all()
    ]