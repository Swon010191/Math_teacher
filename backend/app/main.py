"""Ứng dụng FastAPI của AI Teaching Assistant (backend)."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import copilot, knowledge, math, recognize
from app.services.copilot_settings import get_active_copilot_provider
from app.services.recognition_settings import get_active_provider

app = FastAPI(
    title="AI Teaching Assistant - Math Engine API",
    description=(
        "Nguồn sự thật toán học (SymPy) + Recognition cho AI Teaching Assistant. "
        "Math Core luôn hoạt động, không phụ thuộc Generative AI."
    ),
    version="0.1.0",
)


def _cors_origins() -> list[str]:
    """Địa chỉ frontend được phép gọi API (mặc định Vite dev + bản đóng gói)."""
    raw = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:8000,http://127.0.0.1:8000",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(math.router)
app.include_router(recognize.router)
app.include_router(copilot.router)
app.include_router(knowledge.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Kiểm tra server còn sống + provider nhận dạng/Copilot đang dùng."""
    return {
        "status": "ok",
        "service": "math-engine",
        "recognition_provider": get_active_provider(),
        "copilot_provider": get_active_copilot_provider(),
    }


# Phục vụ frontend đã build (bản đóng gói 1-port): nếu thư mục
# backend/app/static tồn tại (copy từ frontend/dist), mount assets và
# fallback mọi route không phải /api/* về index.html (SPA).
_STATIC_DIR = Path(__file__).resolve().parent / "static"
if _STATIC_DIR.is_dir():  # pragma: no cover - chỉ có ở bản đóng gói
    _assets_dir = _STATIC_DIR / "assets"
    if _assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

    @app.get("/{full_path:path}", tags=["system"], include_in_schema=False)
    def _serve_spa(full_path: str) -> FileResponse:
        first = full_path.split("/", 1)[0]
        if first in {"api", "docs", "openapi.json", "health"}:
            raise HTTPException(status_code=404, detail="Không tìm thấy.")
        candidate = _STATIC_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_STATIC_DIR / "index.html")
