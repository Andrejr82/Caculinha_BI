@echo off
echo ========================================
echo AGENTE BI - MODO LOCAL (SEM DOCKER)
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Iniciando Backend Python...
start "Backend BI" cmd /k "cd backend && .venv\Scripts\activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo [2/3] Iniciando Frontend...
start "Frontend BI" cmd /k "cd frontend-solid && npm run dev"

timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo Sistema iniciado com sucesso!
echo ========================================
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo Docs API: http://localhost:8000/docs
echo.
echo Memoria usada: ~500MB (muito menos que Docker!)
echo ========================================
pause
