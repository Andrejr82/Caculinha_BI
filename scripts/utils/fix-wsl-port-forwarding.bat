@echo off
echo ===================================
echo WSL2 Port Forwarding Fix
echo ===================================
echo.

echo This script will:
echo 1. Get WSL2 IP address
echo 2. Remove old port forwarding rules
echo 3. Create new port forwarding rules for ports 3000 and 8000
echo 4. Allow ports through Windows Firewall
echo.
echo NOTE: This script requires Administrator privileges
echo.
pause

echo [1] Getting WSL2 IP address...
for /f %%i in ('wsl hostname -I') do set WSL_IP=%%i
echo WSL IP: %WSL_IP%
echo.

echo [2] Removing old port forwarding rules (if any)...
netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0 2>nul
netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0 2>nul
echo.

echo [3] Creating new port forwarding rules...
netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=%WSL_IP%
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=%WSL_IP%
echo.

echo [4] Verifying port proxy rules...
netsh interface portproxy show all
echo.

echo [5] Adding Windows Firewall rules...
netsh advfirewall firewall delete rule name="WSL2 Frontend Port 3000" 2>nul
netsh advfirewall firewall delete rule name="WSL2 Backend Port 8000" 2>nul
netsh advfirewall firewall add rule name="WSL2 Frontend Port 3000" dir=in action=allow protocol=TCP localport=3000
netsh advfirewall firewall add rule name="WSL2 Backend Port 8000" dir=in action=allow protocol=TCP localport=8000
echo.

echo [6] Testing connection...
powershell -Command "Test-NetConnection -ComputerName localhost -Port 3000"
echo.

echo ===================================
echo Fix Complete!
echo Try accessing http://localhost:3000 now
echo ===================================
pause
