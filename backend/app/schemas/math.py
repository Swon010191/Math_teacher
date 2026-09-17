from pydantic import BaseModel, Field


class MathAnalyzeRequest(BaseModel):
    """Yêu cầu phân tích một biểu thức toán học."""

    expression: str = Field(..., min_length=1, max_length=500, description="Biểu thức, ví dụ: x**2 - 4*x + 3 hoặc x^2-4x+3")


class MathSolveRequest(MathAnalyzeRequest):
    """Yêu cầu giải phương trình trên miền thực."""

    solve_for: str | None = Field(default=None, max_length=32)


class SolveAnswer(BaseModel):
    exact: str
    latex: str
    approximate: float | None = None
    condition: str | None = None


class SolveStepMetadata(BaseModel):
    """Optional machine-readable meaning for a curriculum solve step."""

    kind: str
    rule: str | None = None
    values: dict[str, str] = Field(default_factory=dict)


class SolveStep(BaseModel):
    expression: str
    explanation: str
    latex: str | None = None
    metadata: SolveStepMetadata | None = None


class SolveCase(BaseModel):
    condition: str
    status: str
    answers: list[SolveAnswer] = Field(default_factory=list)


class MathSolveResponse(BaseModel):
    original_equation: str
    canonical_equation: str
    variables: list[str]
    solve_for: str
    degree: int
    classification: str
    status: str
    answers: list[SolveAnswer] = Field(default_factory=list)
    cases: list[SolveCase] = Field(default_factory=list)
    steps: list[SolveStep]
    verified: bool


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


class RationalFeatures(BaseModel):
    """Đặc trưng của hàm phân thức bậc nhất/bậc nhất y = (ax + b)/(cx + d)."""

    a: float
    b: float
    c: float
    d: float
    poles: list[float] = Field(..., description="Giá trị x hàm số không xác định")
    holes: list[float] = Field(default_factory=list, description="Điểm khuyết do nhân tử bị triệt tiêu")
    vertical_asymptotes: list[str] = Field(..., description="Tiệm cận đứng, ví dụ ['x = 1']")
    horizontal_asymptote: str | None = Field(..., description="Tiệm cận ngang, ví dụ 'y = 2'")
    root: float | None = Field(..., description="Nghiệm của tử số (cắt trục hoành)")
    y_intercept: float | None
    domain: str = Field(..., description="Tập xác định, ví dụ 'x ≠ 1' hoặc 'R'")
    sample_points: list[list[float]]


class TrigFeatures(BaseModel):
    """Đặc trưng của hàm lượng giác y = a*sin(bx + c) + d hoặc a*cos(bx + c) + d."""

    func: str = Field(..., description="'sin' hoặc 'cos'")
    a: float
    b: float
    c: float
    d: float
    amplitude: float
    period: float
    phase_shift: float
    midline: float = Field(..., description="Đường trung bình y = d")
    max_value: float
    min_value: float
    roots: list[float] = Field(..., description="Nghiệm trong cửa sổ hai chu kỳ")
    sample_points: list[list[float]]


class ExponentialFeatures(BaseModel):
    """Đặc trưng của hàm mũ y = a*b^x + c."""

    a: float
    b: float = Field(..., description="Cơ số")
    c: float
    base: float = Field(..., description="Cơ số dùng hiển thị (b hoặc e)")
    direction: str = Field(..., description="Đồng biến/nghịch biến: 'up' hoặc 'down'")
    horizontal_asymptote: str = Field(..., description="Tiệm cận ngang, ví dụ 'y = 0'")
    y_intercept: float
    x_intercept: float | None
    sample_points: list[list[float]]


class LogarithmicFeatures(BaseModel):
    """Đặc trưng của hàm logarit y = a*log(x, base) + c."""

    a: float
    b: float = Field(..., description="Cơ số")
    c: float
    base: float
    domain: str = Field(..., description="Tập xác định, ví dụ 'x > 0'")
    vertical_asymptote: str = Field(..., description="Tiệm cận đứng, ví dụ 'x = 0'")
    x_intercept: float
    sample_points: list[list[float]]


class CalculusFeatures(BaseModel):
    """Đặc trưng calculus: tích phân, tổng, giới hạn, đạo hàm."""

    evaluated_latex: str | None = Field(default=None, description="Dạng đã tính nếu có")
    numeric_value: float | None = Field(default=None, description="Giá trị số nếu khả tính")
    sample_points: list[list[float]] = Field(default_factory=list)


class SpecialFeatures(BaseModel):
    """Đặc trưng hàm đặc biệt: Gamma, erf, beta, zeta, bessel."""

    numeric_value: float | None = Field(default=None)
    sample_points: list[list[float]] = Field(default_factory=list)


class MathAnalyzeResponse(BaseModel):
    """Kết quả phân tích biểu thức."""

    expression: str = Field(..., description="Biểu thức gốc người dùng nhập")
    normalized_expression: str = Field(..., description="Biểu thức đã chuẩn hóa (SymPy)")
    kind: str = Field(
        ...,
        description="Loại: quadratic | linear | rational | trigonometric | exponential | logarithmic | calculus | special | unknown",
    )
    latex: str = Field(..., description="Biểu diễn LaTeX")
    canonical_expression: str | None = Field(
        default=None, description="Biểu thức canonical có thể parse lại"
    )
    source_variable: str = Field(default="x", description="Tên biến nguồn")
    dependent_variable: str | None = Field(
        default=None, description="Tên vế trái nếu đầu vào là định nghĩa hàm"
    )
    quadratic: QuadraticFeatures | None = None
    linear: LinearFeatures | None = None
    rational: RationalFeatures | None = None
    trigonometric: TrigFeatures | None = None
    exponential: ExponentialFeatures | None = None
    logarithmic: LogarithmicFeatures | None = None
    calculus: CalculusFeatures | None = None
    special: SpecialFeatures | None = None
