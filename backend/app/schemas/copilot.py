"""Schemas Teacher Copilot - nội dung sư phạm đề xuất cho một Activity.

Nguyên tắc: mọi số liệu (đỉnh, nghiệm, giao điểm...) đều đến từ Math Engine
(nguồn sự thật); LLM chỉ viết lời văn sư phạm quanh các số liệu đã cho.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CopilotMathInput(BaseModel):
    """Đặc trưng toán học (do Math Engine tính) dùng làm đầu vào cho Copilot."""

    expression: str
    source_variable: str = "x"
    dependent_variable: str | None = None
    a: float | None = None
    b: float | None = None
    c: float | None = None
    d: float | None = None
    func: str | None = None
    base: float | None = None
    root: float | None = None
    vertex: list[float] | None = None
    roots: list[float] | None = None
    axis: str | None = None
    y_intercept: float | None = None
    discriminant: float | None = None
    direction: str | None = None
    amplitude: float | None = None
    period: float | None = None
    phase_shift: float | None = None
    midline: float | None = None
    max_value: float | None = None
    min_value: float | None = None
    asymptotes: list[str] | None = None
    holes: list[float] | None = None
    domain: str | None = None


class CopilotRequest(BaseModel):
    """Yêu cầu đề xuất nội dung giảng dạy cho một Activity đã xác nhận."""

    expression: str = Field(..., min_length=1, max_length=500)
    activity_type: str = Field(..., min_length=1, description="Ví dụ: quadratic_function")
    math: CopilotMathInput
    grade_level: str = Field(default="THCS", max_length=100)


class CopilotExample(BaseModel):
    """Một ví dụ minh họa: câu hỏi và lời giải (số liệu từ Math Engine)."""

    prompt: str
    solution: str


class CopilotSuggestion(BaseModel):
    """Nội dung sư phạm đề xuất; giáo viên phải duyệt trước khi lên bảng."""

    provider: str = ""
    summary: str
    key_points: list[str]
    questions: list[str]
    examples: list[CopilotExample]
    teaching_steps: list[str]
    confidence: float = Field(..., ge=0.0, le=1.0)
