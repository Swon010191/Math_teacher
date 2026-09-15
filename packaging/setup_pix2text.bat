@echo off
REM Cai Pix2Text runtime (nhan dang cong thuc that) bang uv portable.
REM Chay 1 lan luc cai dat (task tuy chon) hoac chay tay sau nay.
setlocal EnableDelayedExpansion

set APPDIR=%~dp0
set RUNTIME=%APPDIR%pix2text-runtime
set UV=%APPDIR%tools\uv.exe
set PYVER=3.12

if not exist "%UV%" (
  echo [LOI] Khong tim thay uv.exe - bo qua Pix2Text.
  exit /b 1
)

echo [1/4] Cai Python %PYVER% (portable, chi dung trong app)...
"%UV%" python install %PYVER% --python-preference only-managed
if errorlevel 1 (
  echo [LOI] Khong tai duoc Python (can mang). App van chay voi Mock.
  exit /b 1
)

echo [2/4] Tao moi truong rieng...
"%UV%" venv "%RUNTIME%\.venv" --python %PYVER% --seed
if errorlevel 1 (
  echo [LOI] Khong tao duoc venv.
  exit /b 1
)

echo [3/4] Cai pix2text + torch CPU (buoc nay nang, cho vai phut)...
"%UV%" pip install --python "%RUNTIME%\.venv\Scripts\python.exe" "pix2text[serve]"
if errorlevel 1 (
  echo [LOI] Khong cai duoc pix2text (can mang).
  exit /b 1
)

echo [4/4] Tai san model nhan dang (lan dau mat vai phut)...
if not defined PIX2TEXT_HOME set PIX2TEXT_HOME=%LOCALAPPDATA%\AI Teaching Assistant\models\.pix2text
"%RUNTIME%\.venv\Scripts\python.exe" -c "from pix2text import Pix2Text; Pix2Text(); print('OK')"
if errorlevel 1 (
  echo [CANH BAO] Chua tai duoc model - mo app len, model se tu tai khi nhan dang.
  exit /b 0
)

echo XONG - Pix2Text san sang.
exit /b 0
