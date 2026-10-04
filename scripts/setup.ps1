# IBVAP Automated Setup Script for Windows PowerShell
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  IBVAP Automated Platform Setup (Windows PowerShell)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Directories
Write-Host "[1/5] Initializing persistent storage directories..." -ForegroundColor Yellow
$dirs = @("blockchain_data", "evidence", "video", "ai_pipeline\output", "scratch_frames", "security")
foreach ($d in $dirs) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Path $d -Force | Out-Null
    }
}

# 2. Reassemble split models if needed
Write-Host "[2/5] Checking and reassembling AI models..." -ForegroundColor Yellow
if (-not (Test-Path "ai_pipeline\epoch_02.pt")) {
    $parts = Get-ChildItem "ai_pipeline\epoch_02.pt.part_*" | Sort-Object Name
    if ($parts) {
        Write-Host "  Reassembling epoch_02.pt from split parts..."
        cmd.exe /c "copy /b ai_pipeline\epoch_02.pt.part_* ai_pipeline\epoch_02.pt"
    }
}

if (-not (Test-Path "yolov8x.pt")) {
    $partsX = Get-ChildItem "yolov8x.pt.part_*" | Sort-Object Name
    if ($partsX) {
        Write-Host "  Reassembling yolov8x.pt from split parts..."
        cmd.exe /c "copy /b yolov8x.pt.part_* yolov8x.pt"
    }
}

# 3. Python dependencies
Write-Host "[3/5] Checking Python..." -ForegroundColor Yellow
python --version

# 4. Frontend build
Write-Host "[4/5] Preparing frontend..." -ForegroundColor Yellow
if (Test-Path "frontend") {
    Set-Location "frontend"
    if (-not (Test-Path "node_modules")) {
        npm install
    }
    npm run build
    Set-Location $Root
}

# 5. Run test
Write-Host "[5/5] Running test suite..." -ForegroundColor Yellow
python test_platform.py

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Setup Complete! Use .\scripts\start.ps1 to run." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
