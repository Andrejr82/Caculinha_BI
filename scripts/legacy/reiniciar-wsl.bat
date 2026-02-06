@echo off
echo ========================================
echo REINICIANDO WSL
echo ========================================
echo.
echo Aplicando configuracoes do .wslconfig...
echo.

wsl --shutdown

echo Aguardando 5 segundos...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo WSL REINICIADO!
echo ========================================
echo.
echo Agora abra o Ubuntu e execute:
echo cd /mnt/c/Agente_BI/BI_Solution
echo ./docker-limpar-tudo.sh
echo.
pause
