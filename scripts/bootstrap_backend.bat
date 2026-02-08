@echo off
setlocal enabledelayedexpansion

echo [INFO] Iniciando bootstrap do backend (Batch)...

set "ROOT=%~dp0.."
set "BACKEND_DIR=%ROOT%\backend"
set "VENV=%ROOT%\.venv"
set "REQ=%BACKEND_DIR%\requirements.txt"

:: 1. Verificar virtualenv
if not exist "%VENV%" (
    echo [INFO] Criando virtualenv (.venv)...
    python -m venv "%VENV%"
    if !errorlevel! neq 0 (
        echo [FAIL] Falha ao criar virtualenv.
        exit /b 1
    )
)

:: 2. Ativar e Sincronizar
echo [INFO] Ativando ambiente e sincronizando dependências...
call "%VENV%\Scripts\activate.bat"

python -m pip install --upgrade pip
pip install pip-tools

if not exist "%REQ%" (
    echo [FAIL] Arquivo requirements.txt não encontrado em %REQ%
    exit /b 1
)

echo [INFO] Executando pip-sync...
python -m piptools sync "%REQ%"

echo [INFO] Executando pip check...
pip check
if !errorlevel! neq 0 (
    echo [FAIL] Inconsistência de dependências detectada pelo pip check!
    exit /b 1
)

echo [OK] Ambiente sincronizado com sucesso.
pause
