@echo off
REM ========================================
REM   AGENT BI - MODO PRODUCAO (WINDOWS NATIVO)
REM   Otimizado para 8GB RAM
REM ========================================

echo.
echo ========================================
echo   AGENT BI - INICIANDO (PRODUCAO)
echo ========================================
echo.

REM 1. Verificar VENV
if not exist "backend\.venv" (
    echo [ERRO] Ambiente virtual nao encontrado.
    echo [INFO] Execute 'setup_windows.bat' primeiro.
    pause
    exit /b 1
)

REM 2. Limpar portas antigas
call npm run clean:ports >nul 2>&1

REM 3. Iniciar Backend (Modo Otimizado - Sem Reload, Multi-workers)
echo [1/2] Iniciando Backend (Uvicorn Production)...
REM --workers 4 permite atender mais usuarios simultaneos
REM --no-access-log economiza IO de disco
start /B cmd /c "cd backend && .venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 > ..\logs\backend_prod.log 2>&1"

REM 4. Aguardar Backend
echo [INFO] Aguardando backend subir...
timeout /t 5 >nul

REM 5. Iniciar Frontend
echo [2/2] Iniciando Frontend...
echo [INFO] Para 30 usuarios, o ideal seria gerar o build estatico.
echo [INFO] Rodando em modo preview para performance...
cd frontend-solid
start cmd /k "pnpm dev --host"
cd ..

echo.
echo ========================================
echo   SISTEMA ONLINE (REDE LOCAL)
echo ========================================
echo.
echo Para acessar de outros computadores, use o IP desta maquina:
echo.
ipconfig | findstr /i "ipv4"
echo.
echo Backend:  http://localhost:8000 (Porta 8000)
echo Frontend: http://localhost:3000 (Porta 3000)
echo.
echo [AVISO] Docker nao esta sendo usado (Economia de RAM).
echo.
pause