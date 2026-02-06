@echo off
echo ===================================
echo WSL2 Docker Network Diagnostic
echo ===================================
echo.

echo [1] Checking Docker containers...
wsl docker ps --filter "name=agent_bi"
echo.

echo [2] Testing if containers are listening on correct ports...
echo --- Frontend container (should listen on 0.0.0.0:80) ---
wsl docker exec agent_bi_frontend netstat -tlnp 2^>^/dev^/null ^|^| wsl docker exec agent_bi_frontend ss -tlnp
echo.

echo --- Backend container (should listen on 0.0.0.0:8000) ---
wsl docker exec agent_bi_backend netstat -tlnp 2^>^/dev^/null ^|^| wsl docker exec agent_bi_backend ss -tlnp
echo.

echo [3] Testing curl from inside frontend container...
wsl docker exec agent_bi_frontend curl -f http://localhost/ -I
echo.

echo [4] Testing curl from WSL to frontend...
wsl curl -f http://localhost:3000 -I
echo.

echo [5] Testing curl from WSL to backend...
wsl curl -f http://localhost:8000/health
echo.

echo [6] Checking Docker bridge network...
wsl docker network inspect bridge ^| grep -A 10 agent_bi
echo.

echo [7] Checking WSL IP address...
wsl hostname -I
echo.

echo [8] Checking if ports are exposed on Windows...
netstat -ano | findstr ":3000"
netstat -ano | findstr ":8000"
echo.

echo [9] Testing from Windows PowerShell to localhost...
powershell -Command "Test-NetConnection -ComputerName localhost -Port 3000"
echo.

echo ===================================
echo Diagnostic Complete
echo ===================================
pause
