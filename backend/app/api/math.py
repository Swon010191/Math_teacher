"""API Math Engine - nguồn sự thật toán học."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.activity import ActivityModel
from app.schemas.math import (
    MathAnalyzeRequest,
    MathAnalyzeResponse,
    MathSolveRequest,
    MathSolveResponse,
)
from app.services.activity_service import build_activity
from app.services.math_service import MathEngineError, analyze_expression, solve_equation

router = APIRouter(prefix="/api/math", tags=["math"])


@router.post("/solve", response_model=MathSolveResponse)
def solve(request: MathSolveRequest) -> MathSolveResponse:
    """Giải phương trình bậc nhất hoặc bậc hai trên miền thực."""
    try:
        return solve_equation(request.expression, request.solve_for)
    except MathEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/analyze", response_model=MathAnalyzeResponse)
def analyze(request: MathAnalyzeRequest) -> MathAnalyzeResponse:
    """Phân tích biểu thức: nhận dạng loại, tính đỉnh/nghiệm/trục đối xứng..."""
    try:
        return analyze_expression(request.expression)
    except MathEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/activity", response_model=ActivityModel)
def create_activity(request: MathAnalyzeRequest) -> ActivityModel:
    """Tạo Activity (hàm bậc hai hoặc bậc nhất) từ biểu thức đã xác nhận."""
    try:
        return build_activity(
            latex=request.expression,
            expression=request.expression,
            confidence=1.0,
            confirmed=True,
        )
    except (MathEngineError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
