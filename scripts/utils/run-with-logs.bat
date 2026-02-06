@echo off
REM ========================================
REM   AGENT BI - COM VISUALIZAÇÃO DE LOGS
REM   Abre 2 terminais: sistema + logs
REM ========================================

echo.
echo ========================================
echo   AGENT BI - INICIANDO COM LOGS
echo ========================================
echo.

REM Limpar processos antigos
echo [1/4] Limpando processos...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nobreak >nul
echo [OK] Processos limpos.
echo.

REM Limpar cache
echo [2/4] Limpando cache...
cd /d "%~dp0backend"
for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
del /s /q *.pyc 2>nul >nul
cd /d "%~dp0"
echo [OK] Cache limpo.
echo.

REM Verificar dependências
echo [3/4] Verificando dependencias...
if not exist node_modules\concurrently (
    echo [INFO] Instalando dependencias...
    call npm install --silent
)
echo [OK] Dependencias verificadas.
echo.

REM Limpar portas
echo [4/4] Limpando portas...
node scripts/clean-port.js
echo.

REM Criar diretórios de logs
if not exist logs mkdir logs
if not exist logs\app mkdir logs\app
if not exist logs\api mkdir logs\api
if not exist logs\security mkdir logs\security
if not exist logs\chat mkdir logs\chat
if not exist logs\errors mkdir logs\errors
if not exist logs\audit mkdir logs\audit

REM Iniciar sistema em um terminal
start "AgentBI - Sistema" cmd /c "npm run dev"

REM Aguardar sistema iniciar
echo [INFO] Aguardando sistema iniciar...
timeout /t 10 /nobreak >nul

REM Iniciar visualizador de logs em outro terminal
start "AgentBI - Logs" cmd /c "npm run logs"

REM Aguardar e abrir navegador
timeout /t 3 /nobreak >nul
start http://localhost:3000

echo.
echo ========================================
echo   2 TERMINAIS ABERTOS
echo ========================================
echo.
echo 1. Sistema (Backend + Frontend)
echo 2. Logs agregados (em tempo real)
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Credenciais:
echo   Username: admin
echo   Senha:    Admin@2024
echo.
echo ========================================
echo.
echo Pressione qualquer tecla para sair...
pause >nul
