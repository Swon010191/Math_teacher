# Cấu hình và hàm dùng chung cho các script quản lý backend + Pix2Text.
# Đường dẫn suy tương đối từ vị trí repo nên không cần sửa khi đổi máy.

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot 'backend'
$BackendPython = Join-Path $BackendDir '.venv\Scripts\python.exe'
$P2TDir = Join-Path $RepoRoot 'ai-tools\pix2text'
$P2TPythonw = Join-Path $P2TDir '.venv\Scripts\pythonw.exe'
$P2TLauncher = Join-Path $P2TDir 'serve_launcher.py'
# Cho phép đổi port qua biến môi trường (khi port mặc định kẹt hoặc đóng gói).
$BackendPort = if ($env:BACKEND_PORT) { [int]$env:BACKEND_PORT } else { 8000 }
$P2TPort = if ($env:P2T_PORT) { [int]$env:P2T_PORT } else { 8503 }

function Test-Port {
    param([int]$Port)
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Get-PortPid {
    param([int]$Port)
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($conn) { return [int]$conn.OwningProcess }
    return $null
}

function Wait-PortUp {
    param([int]$Port, [int]$TimeoutSeconds = 30)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Port -Port $Port) { return $true }
        Start-Sleep -Milliseconds 500
    }
    return (Test-Port -Port $Port)
}

function Start-P2T {
    param([switch]$Wait)
    if (Test-Port -Port $P2TPort) {
        Write-Host "Pix2Text đã chạy sẵn (port $P2TPort) - bỏ qua."
        return $true
    }
    # Chống chạy đúp: đã có tiến trình serve_launcher đang load model thì không bật thêm.
    $existing = @(Get-CimInstance Win32_Process -Filter "Name = 'pythonw.exe'" |
        Where-Object { $_.CommandLine -match 'serve_launcher' })
    if (-not (Test-Path -LiteralPath $P2TPythonw)) {
        Write-Host "Không tìm thấy $P2TPythonw - hãy cài Pix2Text theo README." -ForegroundColor Yellow
        return $false
    }
    if ($existing.Count -eq 0) {
        Start-Process -FilePath $P2TPythonw -ArgumentList ('"{0}"' -f $P2TLauncher) -WorkingDirectory $P2TDir
        Write-Host "Đã gọi Pix2Text (port $P2TPort) - lúc lạnh cần vài phút tải model."
    } else {
        Write-Host ("Pix2Text đang khởi động sẵn (pid {0}) - chờ nó lên port." -f ($existing[0].ProcessId))
    }
    if (-not $Wait) {
        return $true
    }
    if (Wait-PortUp -Port $P2TPort -TimeoutSeconds 300) {
        Write-Host "Pix2Text đã sẵn sàng (port $P2TPort)."
        return $true
    }
    Write-Host "Cảnh báo: port $P2TPort chưa lên sau 300 giây." -ForegroundColor Yellow
    return $false
}

function Stop-P2T {
    $p2tPid = Get-PortPid -Port $P2TPort
    if ($p2tPid) {
        # Chỉ tắt khi đúng tiến trình Pix2Text (tránh giết nhầm app khác giữ port).
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $p2tPid" -ErrorAction SilentlyContinue
        if ($proc -and ($proc.CommandLine -match 'serve_launcher|pix2text|p2t')) {
            try { taskkill /PID $p2tPid /T /F | Out-Null } catch {}
            Write-Host "Đã tắt Pix2Text (pid $p2tPid)."
        } else {
            Write-Host "Port $P2TPort đang bận bởi tiến trình lạ (pid $p2tPid) - không dám tắt." -ForegroundColor Yellow
        }
    } else {
        Write-Host "Pix2Text không đang chạy."
    }
}

function Stop-Backend {
    # Diệt cả cây process uvicorn (cha + con của --reload) theo command line.
    $targets = @(Get-CimInstance Win32_Process -Filter "Name LIKE 'python%'" |
        Where-Object { $_.CommandLine -match 'uvicorn' })
    if ($targets.Count -gt 0) {
        foreach ($p in $targets) {
            try { taskkill /PID $p.ProcessId /T /F | Out-Null } catch {}
        }
        Write-Host ("Đã tắt backend ({0} process)." -f $targets.Count)
    } else {
        Write-Host "Backend không đang chạy."
    }
}
