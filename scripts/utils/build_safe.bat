@echo off
echo ============================================================================
echo   BI SOLUTION - BUILD SEGURO (MODO ECONOMIA DE RAM)
echo ============================================================================
echo.
echo Este script vai construir os containers UM POR UM para evitar travar seu PC.
echo.

REM 1. Construir Backend (Python)
echo [1/3] Construindo Backend (Python)...
wsl docker compose -f docker-compose.light.yml build backend
if %errorlevel% neq 0 (
    echo ERRO ao construir Backend!
    pause
    exit /b %errorlevel%
)
echo Backend construido com sucesso!
echo.

REM 2. Construir Frontend (Node.js)
echo [2/3] Construindo Frontend (Node.js)...
wsl docker compose -f docker-compose.light.yml build frontend
if %errorlevel% neq 0 (
    echo ERRO ao construir Frontend!
    pause
    exit /b %errorlevel%
)
echo Frontend construido com sucesso!
echo.

REM 3. Iniciar tudo
echo [3/3] Iniciando o sistema...
wsl docker compose -f docker-compose.light.yml up -d
if %errorlevel% neq 0 (
    echo ERRO ao iniciar sistema!
    pause
    exit /b %errorlevel%
)

echo.
echo ============================================================================
echo   SUCESSO! O SISTEMA ESTA RODANDO.
echo ============================================================================
echo.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000/docs
echo.
pause
