"""API Math Engine - nguồn sự thật toán học."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.activity import ActivityModel
from app.schemas.math import MathAnalyzeRequest, MathAnalyzeResponse
from app.services.activity_service import build_quadratic_activity
from app.services.math_service import MathEngineError, analyze_expression

router = APIRouter(prefix="/api/math", tags=["math"])


@router.post("/analyze", response_model=MathAnalyzeResponse)
def analyze(request: MathAnalyzeRequest) -> MathAnalyzeResponse:
    """Phân tích biểu thức: nhận dạng loại, tính đỉnh/nghiệm/trục đối xứng..."""
    try:
        return analyze_expression(request.expression)
    except MathEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/activity", response_model=ActivityModel)
def create_activity(request: MathAnalyzeRequest) -> ActivityModel:
    """Tạo Activity hàm bậc hai (schemaVersion 1.0) từ biểu thức đã xác nhận."""
    try:
        return build_quadratic_activity(
            latex=request.expression,
            expression=request.expression,
            confidence=1.0,
            confirmed=True,
        )
    except (MathEngineError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc