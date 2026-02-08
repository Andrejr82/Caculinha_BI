@echo off
REM Bootstrap Script for Caculinha BI Backend (Windows Batch)
REM Deterministic dependency installation using pip-sync

setlocal enabledelayedexpansion

echo ============================================================
echo   Caculinha BI - Backend Bootstrap
echo ============================================================

cd /d %~dp0..

REM 1. Create venv if missing
if not exist ".venv" (
    echo [*] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv
        exit /b 1
    )
)

REM 2. Activate venv
echo [*] Activating virtual environment...
call .venv\Scripts\activate.bat

REM 3. Install pip-tools if missing
pip show pip-tools >nul 2>&1
if errorlevel 1 (
    echo [*] Installing pip-tools...
    pip install pip-tools
)

REM 4. Compile requirements if .in is newer than .txt
echo [*] Checking if requirements need compilation...
if not exist "backend\requirements.txt" (
    echo [*] Compiling requirements.in -> requirements.txt...
    pip-compile backend\requirements.in -o backend\requirements.txt
)

REM 5. Sync dependencies
echo [*] Syncing dependencies with pip-sync...
pip-sync backend\requirements.txt
if errorlevel 1 (
    echo [ERROR] pip-sync failed
    exit /b 1
)

REM 6. Verify dependencies
echo [*] Verifying dependencies...
pip check
if errorlevel 1 (
    echo [WARNING] pip check found issues
)

REM 7. Run verification script
echo [*] Running backend verification...
python scripts\verify_dependencies.py
if errorlevel 1 (
    echo [ERROR] Verification failed
    exit /b 1
)

echo ============================================================
echo   [OK] Bootstrap complete! Ready to run.
echo   Start with: python -m uvicorn backend.main:app --port 8000
echo ============================================================

endlocal
