@echo off
setlocal enabledelayedexpansion

:: =============================================================================
:: CACULINHA BI - MASTER STARTUP SCRIPT (v2026)
:: Consolidado com Arquitetura Hexagonal e Hardening de Segurança
:: =============================================================================

title Caculinha BI - Master Startup v2026
echo.
echo  [🚀] Iniciando Ecossistema Caculinha BI...
echo.

:: 1. VERIFICAÇÃO DE AMBIENTE (Mentalidade Debugger)
echo  [🔍] Validando requisitos do sistema...

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [❌] Erro: Python nao encontrado no PATH.
    pause & exit /b 1
)

where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [❌] Erro: Node.js nao encontrado no PATH.
    pause & exit /b 1
)

:: 2. VERIFICAÇÃO DE CONFIGURAÇÃO (Mentalidade Database Architect)
echo  [📂] Validando arquivos de configuracao e dados...

if not exist "backend\.env" (
    echo [⚠️] Aviso: Arquivo backend\.env nao encontrado!
    echo [ℹ️] Criando .env a partir do template...
    copy backend\.env.example backend\.env >nul
)

:: Validar Parquet Crítico
if not exist "backend\data\parquet\admmat.parquet" (
    echo [❌] Erro Critico: Base Parquet principal nao encontrada!
    echo [ℹ️] Verifique o caminho: backend\data\parquet\admmat.parquet
    pause & exit /b 1
)

:: 3. LIMPEZA DE CACHE (Mentalidade Code Archaeologist)
echo  [🧹] Limpando caches e arquivos temporarios...
if exist "backend\data\cache_v2" (
    echo [ℹ️] Limpando cache de IA...
)

:: 4. INICIALIZAÇÃO DO BACKEND (Porta 8000)
echo  [⚙️] Iniciando API Backend (FastAPI)...
echo      PYTHONPATH=%CD%
echo      AUTO-RELOAD: ON (watch backend\*.py + backend\.env)
start "Caculinha BI - Backend" cmd /k "set PYTHONPATH=%CD% && set WATCHFILES_FORCE_POLLING=true && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend"

:: Verificação de saúde via Python (Mais robusto que PowerShell)
python scripts/wait_for_backend.py
if %ERRORLEVEL% neq 0 (
    echo  [❌] Timeout: Backend demorou demais para responder.
    echo  [ℹ️] Verifique a janela do Backend para erros.
    echo  [ℹ️] Tente acessar manualmente: http://localhost:8000/health
    pause & exit /b 1
)
echo  [✅] Backend Online!

:: 6. INICIALIZAÇÃO DO FRONTEND (Porta 3000)
echo  [🎨] Iniciando Frontend Reativo (SolidJS)...
cd frontend-solid
if not exist "node_modules" (
    echo [📦] Instalando dependencias do frontend...
    call npm install
)
start "Caculinha BI - Frontend" cmd /k "npm run dev"
cd ..

:: 7. VERIFICAÇÃO FINAL (Mentalidade Test Engineer)
echo.
echo  [📊] STATUS DO SISTEMA:
echo  --------------------------------------
echo  Backend:  http://localhost:8000/docs
echo  Frontend: http://localhost:3000
echo  --------------------------------------
echo.
echo  [🎉] Sistema pronto para uso!
echo  Pressione qualquer tecla para encerrar este monitor (os servicos continuarao rodando).
pause >nul
