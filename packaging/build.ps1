# Build bo cai Setup.exe cho AI Teaching Assistant (Windows x64).
# Chay tu thu muc goc repo:  powershell -ExecutionPolicy Bypass -File packaging\build.ps1

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot 'backend'
$FrontendDir = Join-Path $RepoRoot 'frontend'
$PackDir = $PSScriptRoot
$StageDir = Join-Path $PackDir 'stage'
$OutputDir = Join-Path $PackDir 'output'
$BackendPython = Join-Path $BackendDir '.venv\Scripts\python.exe'

$ISCC = @(
    (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'),
    'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',
    'C:\Program Files\Inno Setup 6\ISCC.exe'
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $ISCC) { throw 'Chua cai Inno Setup (can ISCC.exe). Cai: winget install --id JRSoftware.InnoSetup -e' }
if (-not (Test-Path -LiteralPath $BackendPython)) { throw "Khong tim thay venv backend: $BackendPython" }

Write-Host '=== [1/6] Build frontend ==='
& npm --prefix $FrontendDir run build
if ($LASTEXITCODE -ne 0) { throw 'Build frontend that bai' }

Write-Host '=== [2/6] Gop frontend/dist vao backend/app/static ==='
$StaticDir = Join-Path $BackendDir 'app\static'
if (Test-Path -LiteralPath $StaticDir) { Remove-Item -LiteralPath $StaticDir -Recurse -Force }
New-Item -ItemType Directory -Path $StaticDir | Out-Null
Copy-Item -Path (Join-Path $FrontendDir 'dist\*') -Destination $StaticDir -Recurse -Force

Write-Host '=== [3/6] PyInstaller backend (MathBackend) ==='
& $BackendPython -m pip install -q pystray pillow
if ($LASTEXITCODE -ne 0) { throw 'Cai pystray/pillow that bai' }
Push-Location $BackendDir
try {
    & $BackendPython -m PyInstaller --noconfirm --clean --onedir --name MathBackend `
        --paths $BackendDir `
        --add-data "$StaticDir;app/static" `
        --collect-all uvicorn `
        --hidden-import dotenv `
        (Join-Path $PackDir 'server_main.py')
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller backend that bai' }
} finally { Pop-Location }

Write-Host '=== [4/6] PyInstaller launcher ==='
Push-Location $PackDir
try {
    & $BackendPython -m PyInstaller --noconfirm --clean --onefile --noconsole `
        --name AI-Teaching-Assistant `
        --hidden-import pystray --hidden-import PIL `
        (Join-Path $PackDir 'launcher.py')
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller launcher that bai' }
} finally { Pop-Location }

Write-Host '=== [5/6] Chuan bi stage (backend + launcher + uv + script cai AI) ==='
if (Test-Path -LiteralPath $StageDir) { Remove-Item -LiteralPath $StageDir -Recurse -Force }
New-Item -ItemType Directory -Path "$StageDir\tools" | Out-Null
Copy-Item -Path (Join-Path $BackendDir 'dist\MathBackend\*') -Destination "$StageDir\backend" -Recurse -Force
Copy-Item -Path (Join-Path $PackDir 'dist\AI-Teaching-Assistant.exe') -Destination $StageDir -Force
Copy-Item -Path (Join-Path $PackDir 'setup_pix2text.bat') -Destination $StageDir -Force
$UvZip = Join-Path $env:TEMP 'uv-win.zip'
$UvExe = "$StageDir\tools\uv.exe"
if (-not (Test-Path -LiteralPath $UvExe)) {
    Invoke-WebRequest -Uri 'https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip' -OutFile $UvZip
    Expand-Archive -Path $UvZip -DestinationPath (Join-Path $env:TEMP 'uv-win') -Force
    Copy-Item -Path (Join-Path $env:TEMP 'uv-win\uv.exe') -Destination $UvExe -Force
}

Write-Host '=== [6/6] Bien dich Setup.exe (Inno Setup) ==='
if (-not (Test-Path -LiteralPath $OutputDir)) { New-Item -ItemType Directory -Path $OutputDir | Out-Null }
& $ISCC (Join-Path $PackDir 'app.iss')
if ($LASTEXITCODE -ne 0) { throw 'Inno Setup that bai' }

Write-Host ''
Write-Host 'XONG. File cai dat:' -ForegroundColor Green
Get-ChildItem -LiteralPath $OutputDir -Filter 'Setup-*.exe' | ForEach-Object {
    Write-Host ("  {0}  ({1:N1} MB)" -f $_.FullName, ($_.Length / 1MB)) -ForegroundColor Green
}
