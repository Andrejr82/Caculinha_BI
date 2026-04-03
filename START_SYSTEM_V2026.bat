@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
set "LAUNCHER_PS1=%SCRIPT_DIR%scripts\start_system_v2026.ps1"
set "PWSH_EXE="
set "FALLBACK_PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"

if not exist "%LAUNCHER_PS1%" (
    echo [ERRO] Script de inicializacao nao encontrado:
    echo        %LAUNCHER_PS1%
    exit /b 1
)

for %%P in ("%ProgramFiles%\PowerShell\7\pwsh.exe") do (
    if exist "%%~fP" set "PWSH_EXE=%%~fP"
)

if not defined PWSH_EXE (
    for /f "delims=" %%P in ('where pwsh 2^>nul') do (
        if not defined PWSH_EXE set "PWSH_EXE=%%~fP"
    )
)

if not defined PWSH_EXE (
    if exist "%FALLBACK_PS%" (
        set "PWSH_EXE=%FALLBACK_PS%"
    ) else (
        echo [ERRO] Nenhum PowerShell compativel encontrado.
        echo [INFO] Instale o PowerShell 7 ou habilite o Windows PowerShell.
        exit /b 1
    )
)

echo [INFO] Executando inicializacao principal...
"%PWSH_EXE%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%LAUNCHER_PS1%" %*
exit /b %ERRORLEVEL%
