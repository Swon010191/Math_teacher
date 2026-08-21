# Tắt backend + Pix2Text (phương án dọn tay, không cần tìm cửa sổ uvicorn).
. (Join-Path $PSScriptRoot '_common.ps1')
Stop-Backend
Stop-P2T
