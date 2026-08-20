"""API Recognition - nhận dạng nét viết tay/vùng ảnh."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.recognition import RecognizeRequest, RecognizeResult
from app.services.recognition_service import recognize

router = APIRouter(prefix="/api/recognize", tags=["recognition"])


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