# Khởi động backend (uvicorn --reload) + Pix2Text trong 1 lệnh.
# Tắt backend bằng Ctrl+C hoặc đóng cửa sổ -> Pix2Text tự tắt theo (watcher, không poll).
. (Join-Path $PSScriptRoot '_common.ps1')

if (Test-Port -Port $BackendPort) {
    # Port bận chưa chắc là backend của mình - kiểm tra /health trước khi bỏ qua.
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:$BackendPort/health" -TimeoutSec 5
        if ($health.service -eq 'math-engine') {
            Write-Host "Backend đã chạy sẵn (port $BackendPort) - không khởi động lại."
            exit 0
        }
    } catch {}
    Write-Host "Port $BackendPort đang bận bởi dịch vụ lạ - hãy đổi port bằng biến môi trường BACKEND_PORT." -ForegroundColor Yellow
    exit 1
}

Write-Host "Đang khởi động backend (uvicorn --reload, port $BackendPort)..."
$uvicorn = Start-Process -FilePath $BackendPython `
    -ArgumentList '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', "$BackendPort", '--reload' `
    -WorkingDirectory $BackendDir -PassThru
if (-not $uvicorn) {
    Write-Host "Không khởi động được backend." -ForegroundColor Red
    exit 1
}

if (Wait-PortUp -Port $BackendPort -TimeoutSeconds 30) {
    Write-Host "Backend đã chạy (port $BackendPort)."
} else {
    Write-Host "Cảnh báo: port $BackendPort chưa lên sau 30 giây." -ForegroundColor Yellow
}

Start-P2T

# Watcher ẩn: chờ tiến trình uvicorn thoát rồi tắt Pix2Text ngay lập tức.
$commonPath = Join-Path $PSScriptRoot '_common.ps1'
$watcherCmd = ". '{0}'; Wait-Process -Id {1} -ErrorAction SilentlyContinue; Stop-P2T" -f $commonPath, $uvicorn.Id
Start-Process -FilePath 'powershell.exe' `
    -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-Command', $watcherCmd | Out-Null
Write-Host "Watcher đang theo dõi backend (pid $($uvicorn.Id)) - tắt backend là Pix2Text cũng tắt."
