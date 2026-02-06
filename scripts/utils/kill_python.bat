@echo off
echo Encerrando processos Python...
taskkill /F /IM python.exe
taskkill /F /IM npx.cmd
taskkill /F /IM node.exe
echo.
echo Processos encerrados!
pause
