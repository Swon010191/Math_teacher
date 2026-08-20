from pydantic import BaseModel, Field


class MathAnalyzeRequest(BaseModel):
    """Yêu cầu phân tích một biểu thức toán học."""

    expression: str = Field(..., min_length=1, max_length=500, description="Biểu thức, ví dụ: x**2 - 4*x + 3 hoặc x^2-4x+3")


class QuadraticFeatures(BaseModel):
    """Đặc trưng của hàm bậc hai y = ax^2 + bx + c."""

    a: float
    b: float
    c: float
    discriminant: float
    vertex: list[float] = Field(..., description="Đỉnh [h, k]")
    axis: str = Field(..., description="Trục đối xứng, ví dụ 'x = 2'")
    roots: list[float] = Field(..., description="Nghiệm thực")
    y_intercept: float
    direction: str = Field(..., description="Bề lõm: 'up' hoặc 'down'")
    sample_points: list[list[float]] = Field(..., description="Điểm mẫu [x, y] cho đồ thị")


class LinearFeatures(BaseModel):
    """Đặc trưng của hàm bậc nhất y = ax + b."""

    a: float
    b: float
    root: float | None
    y_intercept: float
    sample_points: list[list[float]]


class MathAnalyzeResponse(BaseModel):
    """Kết quả phân tích biểu thức."""

    expression: str = Field(..., description="Biểu thức gốc người dùng nhập")
    normalized_expression: str = Field(..., description="Biểu thức đã chuẩn hóa (SymPy)")
    kind: str = Field(..., description="Loại: quadratic | linear | unknown")
    latex: str = Field(..., description="Biểu diễn LaTeX")
    quadratic: QuadraticFeatures | None = None
    linear: LinearFeatures | None = None