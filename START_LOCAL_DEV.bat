@echo off
REM ============================================================================
REM START_LOCAL_DEV.bat - Inicializador Simplificado
REM ============================================================================

echo.
echo ============================================================================
echo    BI_Solution v2.0 - Ambiente de Desenvolvimento Local
echo ============================================================================
echo.

REM Mudar para o diretorio do projeto
cd /d "%~dp0"

echo [1/4] Validando pre-requisitos...

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    pause
    exit /b 1
)
echo   OK - Python instalado

REM Verificar Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Node.js nao encontrado!
    pause
    exit /b 1
)
echo   OK - Node.js instalado

echo.
echo [2/4] Limpando processos antigos...

REM Matar processos nas portas 8000 e 3000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1

echo   OK - Portas liberadas

echo.
echo [3/4] Iniciando Backend (porta 8000)...

REM Iniciar backend em nova janela (sem abrir browser)
start "BI Backend" cmd /k "cd /d "%~dp0backend" && python main.py"

echo   Aguardando backend inicializar...
timeout /t 5 /nobreak >nul

echo   OK - Backend iniciado

echo.
echo [4/4] Iniciando Frontend (porta 3000)...

REM Iniciar frontend em nova janela (sem --open, para nao abrir browser duas vezes)
start "BI Frontend" cmd /k "cd /d "%~dp0frontend-solid" && npm run dev"

echo   Aguardando frontend inicializar...
timeout /t 8 /nobreak >nul

echo   OK - Frontend iniciado

echo.
echo ============================================================================
echo    AMBIENTE PRONTO!
echo ============================================================================
echo.
echo URLs de Acesso:
echo   - Frontend: http://localhost:3000
echo   - Backend:  http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo.
echo Os servidores estao rodando em janelas separadas.
echo Para parar, feche as janelas "BI Backend" e "BI Frontend".
echo.

REM Loop para aguardar Backend (8000) e Frontend (3000) estarem ouvindo
echo.
echo [5/5] Aguardando servicos ficarem online...

:WAIT_LOOP
timeout /t 2 /nobreak >nul

REM Check Backend Port 8000 (Simplified check)
netstat -ano | findstr ":8000" >nul
if errorlevel 1 (
    echo   - Aguardando Backend (8000)...
    goto WAIT_LOOP
)

REM Check Frontend Port 3000 (Simplified check)
netstat -ano | findstr ":3000" >nul
if errorlevel 1 (
    echo   - Aguardando Frontend (3000)...
    goto WAIT_LOOP
)

echo   OK - Todos os servicos estao online!
echo.

REM Abrir browser APENAS uma vez no endereco correto
echo Abrindo navegador em http://localhost:3000 ...
start "" "http://localhost:3000"

echo.
echo Pressione qualquer tecla para fechar esta janela...
pause >nul
