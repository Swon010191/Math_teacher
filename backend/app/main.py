"""Ứng dụng FastAPI của AI Teaching Assistant (backend)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import math, recognize
from app.services.recognition_settings import get_active_provider

app = FastAPI(
    title="AI Teaching Assistant - Math Engine API",
    description=(
        "Nguồn sự thật toán học (SymPy) + Recognition cho AI Teaching Assistant. "
        "Math Core luôn hoạt động, không phụ thuộc Generative AI."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(math.router)
app.include_router(recognize.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Kiểm tra server còn sống + provider nhận dạng đang dùng."""
    return {
        "status": "ok",
        "service": "math-engine",
        "recognition_provider": get_active_provider(),
    }