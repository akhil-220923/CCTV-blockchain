# IBVAP Start Script for Windows PowerShell
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "Starting IBVAP Backend on port 5000..." -ForegroundColor Cyan
Start-Process -NoNewWindow python -ArgumentList "web\server.py"

Write-Host "Starting Frontend Command Center on port 3000..." -ForegroundColor Cyan
Set-Location "frontend"
Start-Process -NoNewWindow npm -ArgumentList "run dev -- --host 0.0.0.0 --port 3000"

Write-Host "Services started! Open http://localhost:3000 in your browser." -ForegroundColor Green
