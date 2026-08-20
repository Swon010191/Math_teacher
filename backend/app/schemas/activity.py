from pydantic import BaseModel, Field


class ActivitySource(BaseModel):
    """Nguồn gốc biểu thức của activity."""

    latex: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    confirmed: bool = True


class ActivityMath(BaseModel):
    """Kết quả chính xác từ Math Engine."""

    expression: str
    a: float | None = None
    b: float | None = None
    c: float | None = None
    root: float | None = None
    vertex: list[float] | None = None
    roots: list[float] | None = None
    axis: str | None = None
    y_intercept: float | None = None
    discriminant: float | None = None
    direction: str | None = None


class ActivityWidget(BaseModel):
    """Widget trong activity."""

    type: str
    parameters: list[str] | None = None


class ActivityStep(BaseModel):
    """Một bước trong chuỗi giảng dạy: các thành phần hiển thị."""

    visible: list[str]


class ActivityModel(BaseModel):
    """Định dạng mở của một Teaching Activity (schemaVersion 1.0)."""

    schemaVersion: str = "1.0"
    type: str
    source: ActivitySource
    math: ActivityMath
    widgets: list[ActivityWidget]
    steps: list[ActivityStep]