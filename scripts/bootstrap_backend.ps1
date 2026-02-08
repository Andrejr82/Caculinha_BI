# Bootstrap Script for Caculinha BI Backend (PowerShell)
# Deterministic dependency installation using pip-sync

param(
    [switch]$Force,
    [switch]$Compile
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Caculinha BI - Backend Bootstrap (PowerShell)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Push-Location (Split-Path -Parent $PSScriptRoot)

try {
    # 1. Create venv if missing
    if (-not (Test-Path ".venv") -or $Force) {
        Write-Host "[*] Creating virtual environment..." -ForegroundColor Yellow
        python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw "Failed to create venv" }
    }

    # 2. Activate venv
    Write-Host "[*] Activating virtual environment..." -ForegroundColor Yellow
    & .\.venv\Scripts\Activate.ps1

    # 3. Install pip-tools if missing
    $pipTools = pip show pip-tools 2>$null
    if (-not $pipTools) {
        Write-Host "[*] Installing pip-tools..." -ForegroundColor Yellow
        pip install pip-tools
    }

    # 4. Compile requirements if requested or .txt missing
    if ($Compile -or -not (Test-Path "backend\requirements.txt")) {
        Write-Host "[*] Compiling requirements.in -> requirements.txt..." -ForegroundColor Yellow
        pip-compile backend\requirements.in -o backend\requirements.txt
        if ($LASTEXITCODE -ne 0) { throw "pip-compile failed" }
    }

    # 5. Sync dependencies
    Write-Host "[*] Syncing dependencies with pip-sync..." -ForegroundColor Yellow
    pip-sync backend\requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "pip-sync failed" }

    # 6. Verify dependencies
    Write-Host "[*] Verifying dependencies..." -ForegroundColor Yellow
    pip check
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[WARNING] pip check found issues" -ForegroundColor DarkYellow
    }

    # 7. Run verification script
    Write-Host "[*] Running backend verification..." -ForegroundColor Yellow
    python scripts\verify_dependencies.py
    if ($LASTEXITCODE -ne 0) { throw "Verification failed" }

    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  [OK] Bootstrap complete! Ready to run." -ForegroundColor Green
    Write-Host "  Start with: python -m uvicorn backend.main:app --port 8000" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
}
catch {
    Write-Host "[ERROR] $_" -ForegroundColor Red
    exit 1
}
finally {
    Pop-Location
}
