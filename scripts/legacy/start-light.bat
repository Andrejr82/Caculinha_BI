@echo off
echo ========================================
echo AGENTE BI - MODO LEVE (8GB RAM)
echo ========================================
echo.

echo [1/3] Reiniciando WSL para aplicar configuracoes...
wsl --shutdown
timeout /t 3 /nobreak >nul

echo.
echo [2/3] Iniciando Docker em modo otimizado...
docker-compose -f docker-compose.light.yml up -d

echo.
echo [3/3] Aguardando servicos...
timeout /t 10 /nobreak >nul

echo.
echo ========================================
echo Sistema iniciado com sucesso!
echo ========================================
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo Docs API: http://localhost:8000/docs
echo.
echo Uso de memoria limitado a ~1.2GB
echo ========================================
echo.
echo Para parar: docker-compose -f docker-compose.light.yml down
pause
