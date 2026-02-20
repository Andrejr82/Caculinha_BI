@echo off
setlocal EnableDelayedExpansion

REM =============================================================================
REM CACULINHA BI - MASTER STARTUP SCRIPT (v2026)
REM =============================================================================

chcp 65001 >nul
title Caculinha BI - Master Startup v2026

echo.
echo [START] Iniciando ecossistema Caculinha BI...
echo.

REM 1) Validacao de ambiente
echo [CHECK] Validando requisitos...

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERRO] Python nao encontrado no PATH.
    pause
    exit /b 1
)

where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERRO] Node.js nao encontrado no PATH.
    pause
    exit /b 1
)

REM 2) Validacao de configuracao
echo [CHECK] Validando arquivos de configuracao e dados...

if not exist "backend\.env" (
    echo [WARN] backend\.env nao encontrado.
    echo [INFO] Criando backend\.env a partir de backend\.env.example...
    copy "backend\.env.example" "backend\.env" >nul
)

if not exist "backend\data\parquet\admmat.parquet" (
    echo [ERRO] Base parquet principal nao encontrada.
    echo [INFO] Caminho esperado: backend\data\parquet\admmat.parquet
    pause
    exit /b 1
)

REM 3) Limpeza preventiva de portas para evitar conflito no npm/vite e uvicorn
echo [CHECK] Liberando portas 8000 e 3000, se necessario...
call :KillPort 8000
call :KillPort 3000

REM 4) Backend
echo [BACKEND] Iniciando API FastAPI em 8000...
echo         PYTHONPATH=%CD%
start "Caculinha BI - Backend" cmd /k "set PYTHONPATH=%CD% && set WATCHFILES_FORCE_POLLING=true && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend --reload-include *.py --reload-include .env"

python scripts/wait_for_backend.py
if %ERRORLEVEL% neq 0 (
    echo [ERRO] Timeout: backend nao respondeu no tempo esperado.
    echo [INFO] Verifique a janela do backend.
    echo [INFO] URL de teste: http://localhost:8000/health
    pause
    exit /b 1
)
echo [OK] Backend online.

REM 5) Frontend
echo [FRONTEND] Iniciando SolidJS em 3000...
pushd "frontend-solid"
if not exist "node_modules" (
    echo [INFO] Instalando dependencias do frontend...
    call npm install
    if %ERRORLEVEL% neq 0 (
        echo [ERRO] Falha ao instalar dependencias do frontend.
        popd
        pause
        exit /b 1
    )
)
start "Caculinha BI - Frontend" cmd /k "npm run dev -- --host 127.0.0.1 --port 3000"
popd

echo.
echo [STATUS] Sistema iniciado:
echo --------------------------------------
echo Backend : http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo --------------------------------------
echo.
echo [DONE] Pode fechar esta janela. Backend e frontend continuam rodando.
pause >nul
exit /b 0

:KillPort
set "PORT=%~1"
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%PORT% .*LISTENING"') do (
    echo [INFO] Porta %PORT% ocupada pelo PID %%P. Encerrando...
    taskkill /PID %%P /F >nul 2>nul
)
exit /b 0
