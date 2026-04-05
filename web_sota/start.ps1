# Webapp Start - Standardized SOTA (Auto-Repaired V2.5)
$WebPort = 10884
$BackendPort = 10885
$StudioPort = 10930
$StudioDir = if ($env:SONGGEN_STUDIO_DIR) { $env:SONGGEN_STUDIO_DIR } else { "D:\Dev\repos\external\SongGeneration-Studio" }
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# 1. Kill any process squatting on the ports
Write-Host "Checking for port squatters on $WebPort and $BackendPort..." -ForegroundColor Yellow
$pids = Get-NetTCPConnection -LocalPort $WebPort, $BackendPort -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -gt 4 } | Select-Object -ExpandProperty OwningProcess -Unique
foreach ($p in $pids) {
    Write-Host "Found squatter (PID: $p). Terminating..." -ForegroundColor Red
    try { Stop-Process -Id $p -Force -ErrorAction Stop } catch { Write-Host "Warning: Could not terminate PID $p." -ForegroundColor Gray }
}

# 1b. Ensure SongGeneration-Studio is running (local default)
$studioListener = Get-NetTCPConnection -LocalPort $StudioPort -State Listen -ErrorAction SilentlyContinue
if (-not $studioListener) {
    $studioMain = Join-Path $StudioDir "main.py"
    if (Test-Path $studioMain) {
        Write-Host "Starting SongGeneration-Studio on port $StudioPort ..." -ForegroundColor Cyan
        $studioCmd = "Set-Location '$StudioDir'; python main.py --host 127.0.0.1 --port $StudioPort"
        Start-Process powershell -ArgumentList "-NoExit", "-Command", $studioCmd -WindowStyle Normal
        Start-Sleep -Seconds 2
    } else {
        Write-Host "SongGeneration-Studio not found at $StudioDir (set SONGGEN_STUDIO_DIR)." -ForegroundColor Yellow
    }
}

# 2. Setup
Set-Location $PSScriptRoot
if (-not (Test-Path "node_modules")) { npm install }

# 3. Start the Python backend (Background)
Write-Host "Starting Python backend on port $BackendPort ..." -ForegroundColor Cyan

# Use TRIPLE backtick to ensure $env:PYTHONPATH reaches the REAL shell
$backendCmd = "`$env:PYTHONPATH = '$ProjectRoot\src'; Set-Location '$ProjectRoot'; uv run uvicorn songgeneration_mcp.server:app --host 127.0.0.1 --port $BackendPort --log-level info"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Normal

# 4. Run server (Vite dev)
Write-Host "Starting Vite frontend on port $WebPort ..." -ForegroundColor Green

# 4b. Launch background task to open browser once frontend is ready (Auto-opened by Antigravity)
$frontendUrl = "http://127.0.0.1:$WebPort/"
$pollAndOpen = "for (`$i = 0; `$i -lt 60; `$i++) { try { `$null = Invoke-WebRequest -Uri '$frontendUrl' -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop; Start-Process '$frontendUrl'; exit } catch { Start-Sleep -Seconds 1 } }"
Start-Process powershell -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-Command", $pollAndOpen

Write-Host "Browser will open automatically when Vite is ready." -ForegroundColor Gray
npm run dev -- --port $WebPort --host



