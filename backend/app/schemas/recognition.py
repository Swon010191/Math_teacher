from pydantic import BaseModel, Field


class RecognizeRequest(BaseModel):
    """Yêu cầu nhận dạng nét viết tay / vùng ảnh."""

    image_base64: str | None = Field(
        default=None, description="Ảnh vùng được chọn dạng base64 (tùy chọn trong Mock)"
    )
    hint: str | None = Field(
        default=None, description="Gợi ý văn bản kèm theo vùng chọn (nếu có)"
    )


class RecognizeResult(BaseModel):
    """Kết quả nhận dạng."""

    latex: str = Field(..., description="Công thức dạng LaTeX")
    expression: str = Field(
        ...,
        description="Công thức/phương trình chuẩn hóa, bảo toàn vế trái và dấu bằng",
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Độ tin cậy 0..1")
    provider: str = Field(..., description="Tên provider đã xử lý (mock, ollama_vision, pix2text...)")
    raw: str | None = Field(default=None, description="Kết quả thô của model (nếu có)")
