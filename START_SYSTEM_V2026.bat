@echo off
setlocal EnableDelayedExpansion

REM =============================================================================
REM CACULINHA BI - MASTER STARTUP SCRIPT (v2026)
REM =============================================================================

chcp 65001 >nul
title Caculinha BI - Master Startup v2026

REM [AJUSTE] Lock de execucao (evita duas instancias simultaneas deste script)
REM           Se quiser outro lock por projeto, ajuste o nome abaixo.
set "LOCK_DIR=%TEMP%\caculinha_bi_start_v2026.lock"
2>nul mkdir "%LOCK_DIR%"
if errorlevel 1 (
    echo [INFO] Execucao duplicada detectada. Reiniciando servicos em andamento...
    call :KillWindowByTitle "Caculinha BI - Backend"
    call :KillWindowByTitle "Caculinha BI - Frontend"
    call :KillPort 8000
    call :KillPort 3000
    timeout /t 1 >nul
    2>nul rmdir "%LOCK_DIR%"
    2>nul mkdir "%LOCK_DIR%"
    if errorlevel 1 (
        echo [ERRO] Nao foi possivel atualizar lock para reinicializacao.
        exit /b 1
    )
)

echo.
echo [START] Iniciando ecossistema Caculinha BI...
echo.

REM 1) Validacao de ambiente
echo [CHECK] Validando requisitos...

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERRO] Python nao encontrado no PATH.
    pause
    goto :EXIT_ERROR
)

set "BUN_CMD="
for /f "delims=" %%B in ('where bun 2^>nul') do (
    if not defined BUN_CMD set "BUN_CMD=%%~fB"
)
if not defined BUN_CMD (
    if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages\Oven-sh.Bun_Microsoft.Winget.Source_8wekyb3d8bbwe\bun-windows-x64\bun.exe" (
        set "BUN_CMD=%LOCALAPPDATA%\Microsoft\WinGet\Packages\Oven-sh.Bun_Microsoft.Winget.Source_8wekyb3d8bbwe\bun-windows-x64\bun.exe"
    ) else if exist "%USERPROFILE%\.bun\bin\bun.exe" (
        set "BUN_CMD=%USERPROFILE%\.bun\bin\bun.exe"
    ) else (
        echo [ERRO] Bun nao encontrado no PATH.
        echo [INFO] Instale o Bun e reabra o terminal.
        pause
        goto :EXIT_ERROR
    )
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
    goto :EXIT_ERROR
)

REM 3) Limpeza preventiva de portas para evitar conflito no bun/vite e uvicorn
REM [AJUSTE] Portas padrao do ecossistema local
REM - 8000: backend FastAPI
REM - 3000: frontend Solid/Vite
echo [CHECK] Liberando portas 8000 e 3000, se necessario...
call :KillPort 8000
call :KillPort 3000

REM 4) Backend
REM [AJUSTE] Comando do backend local com auto-reload
REM - HOST/PORT podem ser alterados diretamente na linha do uvicorn
REM - WATCHFILES_FORCE_POLLING=true melhora confiabilidade de reload no Windows
REM - --reload-include inclui alteracoes em Python e .env
echo [BACKEND] Iniciando API FastAPI em 8000...
echo         PYTHONPATH=%CD%
call :WindowExists "Caculinha BI - Backend"
if not errorlevel 1 (
    echo [INFO] Janela do backend ja esta aberta. Pulando abertura duplicada.
) else (
    start "Caculinha BI - Backend" cmd /k "set PYTHONPATH=%CD% && set WATCHFILES_FORCE_POLLING=true && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend --reload-include *.py --reload-include .env"
)

REM ---------------------------------------------------------------------------
REM [PONTO MAIS IMPORTANTE - ESPERA DO FRONTEND]
REM O frontend SO sobe depois que o backend estiver pronto.
REM
REM Este comando chama o arquivo:
REM   scripts/wait_for_backend.py
REM
REM O que ele faz:
REM 1) Espera a porta 8000 abrir.
REM 2) Testa http://localhost:8000/health
REM 3) So continua para o frontend se o backend responder OK (HTTP 200).
REM
REM Se quiser mudar tempo de espera/host/porta:
REM - Edite scripts/wait_for_backend.py (comentado linha a linha).
REM ---------------------------------------------------------------------------
python scripts/wait_for_backend.py
if %ERRORLEVEL% neq 0 (
    echo [ERRO] Timeout: backend nao respondeu no tempo esperado.
    echo [INFO] Verifique a janela do backend.
    echo [INFO] URL de teste: http://localhost:8000/health
    pause
    goto :EXIT_ERROR
)
echo [OK] Backend online.

REM 5) Frontend
REM [AJUSTE] Host/porta do frontend (Vite dev server)
REM [REGRA] Este bloco so executa se o wait_for_backend.py retornar sucesso.
echo [FRONTEND] Iniciando SolidJS em 3000...
pushd "frontend-solid"
if not exist "node_modules" (
    echo [INFO] Instalando dependencias do frontend...
    call "%BUN_CMD%" install
    if %ERRORLEVEL% neq 0 (
        echo [ERRO] Falha ao instalar dependencias do frontend.
        popd
        pause
        goto :EXIT_ERROR
    )
)
call :WindowExists "Caculinha BI - Frontend"
if not errorlevel 1 (
    echo [INFO] Janela do frontend ja esta aberta. Pulando abertura duplicada.
) else (
    start "Caculinha BI - Frontend" cmd /k ""%BUN_CMD%" run dev -- --host 127.0.0.1 --port 3000"
)
popd

echo.
echo [STATUS] Sistema iniciado:
echo --------------------------------------
REM [AJUSTE] URLs finais de acesso local
echo Backend : http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo --------------------------------------
echo.
echo [DONE] Pode fechar esta janela. Backend e frontend continuam rodando.
pause >nul
goto :EXIT_OK

:KillPort
set "PORT=%~1"
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%PORT% .*LISTENING"') do (
    echo [INFO] Porta %PORT% ocupada pelo PID %%P. Encerrando...
    taskkill /PID %%P /F >nul 2>nul
)
exit /b 0

:WindowExists
set "WINDOW_TITLE=%~1"
tasklist /v /fi "IMAGENAME eq cmd.exe" /fo csv | findstr /i /c:"\"%WINDOW_TITLE%\"" >nul
exit /b %ERRORLEVEL%

:KillWindowByTitle
set "WINDOW_TITLE=%~1"
echo [INFO] Encerrando janelas "%WINDOW_TITLE%"...
taskkill /FI "WINDOWTITLE eq %WINDOW_TITLE%*" /T /F >nul 2>nul
exit /b 0

:IsPortListening
set "PORT=%~1"
netstat -ano | findstr /R /C:":%PORT% .*LISTENING" >nul
exit /b %ERRORLEVEL%

:Cleanup
if exist "%LOCK_DIR%" rmdir "%LOCK_DIR%" >nul 2>nul
exit /b 0

:EXIT_OK
call :Cleanup
exit /b 0

:EXIT_ERROR
call :Cleanup
exit /b 1
