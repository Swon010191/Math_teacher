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
$Version = if ($env:APP_VERSION -match '^\d+\.\d+\.\d+(?:[-+].*)?$') { $env:APP_VERSION } else { '1.0.0' }

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
& $BackendPython -m pip install -q -r (Join-Path $BackendDir 'requirements.lock')
if ($LASTEXITCODE -ne 0) { throw 'Cai dependency tu requirements.lock that bai' }
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
New-Item -ItemType Directory -Path "$StageDir\backend" -Force | Out-Null
Get-ChildItem -LiteralPath (Join-Path $BackendDir 'dist\MathBackend') -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path "$StageDir\backend" $_.Name) -Recurse -Force
}
Copy-Item -Path (Join-Path $PackDir 'dist\AI-Teaching-Assistant.exe') -Destination $StageDir -Force
Copy-Item -Path (Join-Path $PackDir 'setup_pix2text.bat') -Destination $StageDir -Force
$UvZip = Join-Path $env:TEMP 'uv-0.12.15-win.zip'
$UvExe = "$StageDir\tools\uv.exe"
if (-not (Test-Path -LiteralPath $UvExe)) {
    Invoke-WebRequest -Uri 'https://github.com/astral-sh/uv/releases/download/0.12.15/uv-x86_64-pc-windows-msvc.zip' -OutFile $UvZip
    if ((Get-FileHash -LiteralPath $UvZip -Algorithm SHA256).Hash.ToLower() -ne '477bd99a84e34891f2bd4c9152ddeb74e971accccbc59c0f0301f11f08a32d46') { throw 'uv checksum mismatch' }
    Expand-Archive -Path $UvZip -DestinationPath (Join-Path $env:TEMP 'uv-win') -Force
    Copy-Item -Path (Join-Path $env:TEMP 'uv-win\uv.exe') -Destination $UvExe -Force
}

Write-Host '=== [6/6] Bien dich Setup.exe (Inno Setup) ==='
if (-not (Test-Path -LiteralPath $OutputDir)) { New-Item -ItemType Directory -Path $OutputDir | Out-Null }
& $ISCC "/DMyAppVersion=$Version" (Join-Path $PackDir 'app.iss')
if ($LASTEXITCODE -ne 0) { throw 'Inno Setup that bai' }
$PortableZip = Join-Path $OutputDir ("AI-Teaching-Assistant-{0}-windows-x64.zip" -f $Version)
Compress-Archive -Path (Join-Path $StageDir '*') -DestinationPath $PortableZip -CompressionLevel Optimal -Force

Write-Host ''
Write-Host 'XONG. File cai dat:' -ForegroundColor Green
Get-ChildItem -LiteralPath $OutputDir -Filter 'Setup-*.exe' | ForEach-Object {
  Write-Host ("  {0}  ({1:N1} MB)" -f $_.FullName, ($_.Length / 1MB)) -ForegroundColor Green
}
if (Test-Path -LiteralPath $PortableZip) {
    Write-Host ("  {0}  ({1:N1} MB)" -f $PortableZip, ((Get-Item -LiteralPath $PortableZip).Length / 1MB)) -ForegroundColor Green
}
$Checksums = Join-Path $OutputDir ("SHA256SUMS-{0}.txt" -f $Version)
Get-ChildItem -LiteralPath $OutputDir -File -Include 'Setup-*.exe', '*.zip' |
    Get-FileHash -Algorithm SHA256 |
    ForEach-Object { "{0}  {1}" -f $_.Hash.ToLower(), (Split-Path -Leaf $_.Path) } |
    Set-Content -LiteralPath $Checksums -Encoding ASCII
Write-Host ("  {0}" -f $Checksums) -ForegroundColor Green
