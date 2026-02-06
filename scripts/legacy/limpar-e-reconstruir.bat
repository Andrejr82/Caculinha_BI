@echo off
echo ========================================
echo LIMPEZA COMPLETA E RECONSTRUCAO
echo ========================================
echo.
echo ATENCAO: Este script vai:
echo - Parar todos os containers
echo - Remover todos os containers
echo - Remover todas as imagens Docker
echo - Limpar volumes e cache
echo - Reconstruir apenas modo LIGHT
echo.
pause
echo.

echo [1/6] Parando todos os containers...
docker-compose -f docker-compose.yml down 2>nul
docker-compose -f docker-compose.light.yml down 2>nul
docker stop $(docker ps -aq) 2>nul

echo.
echo [2/6] Removendo containers...
docker rm -f $(docker ps -aq) 2>nul

echo.
echo [3/6] Removendo imagens antigas...
docker rmi -f $(docker images -q) 2>nul

echo.
echo [4/6] Limpando volumes e cache...
docker volume prune -f
docker system prune -af --volumes

echo.
echo [5/6] Reiniciando WSL para aplicar configuracoes...
wsl --shutdown
timeout /t 5 /nobreak >nul

echo.
echo [6/6] Reconstruindo modo LIGHT do zero...
docker-compose -f docker-compose.light.yml build --no-cache
docker-compose -f docker-compose.light.yml up -d

echo.
echo ========================================
echo LIMPEZA E RECONSTRUCAO CONCLUIDAS!
echo ========================================
echo.
echo Aguardando inicializacao dos servicos...
timeout /t 15 /nobreak >nul

echo.
echo Verificando status...
docker-compose -f docker-compose.light.yml ps

echo.
echo ========================================
echo SISTEMA PRONTO!
echo ========================================
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo Docs API: http://localhost:8000/docs
echo.
echo Uso de memoria: ~1.2GB
echo ========================================
echo.
pause
