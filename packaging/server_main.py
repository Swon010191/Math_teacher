"""Entry point cho bản đóng gói: chạy Math Engine API bằng uvicorn.

Port đọc từ MATH_BACKEND_PORT (mặc định 8000). Launcher truyền port trống
đã chọn sẵn qua biến môi trường này.
"""

from __future__ import annotations

import os

import uvicorn

# Import truc tiep (khong dung chuoi "app.main:app") de PyInstaller
# phat hien va dong goi toan bo package app.
from app.main import app  # noqa: F401


def main() -> None:
    port = int(os.environ.get("MATH_BACKEND_PORT", "8000"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
