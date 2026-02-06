@echo off
echo ========================================
echo TESTE RAPIDO DO AMBIENTE
echo ========================================
echo.

echo [1/4] Testando Python...
python --version
if errorlevel 1 (
    echo ❌ Python nao encontrado
    pause
    exit /b 1
)
echo ✅ Python OK
echo.

echo [2/4] Testando Node.js...
node --version
if errorlevel 1 (
    echo ❌ Node.js nao encontrado
    pause
    exit /b 1
)
echo ✅ Node.js OK
echo.

echo [3/4] Testando Backend...
cd backend
call .venv\Scripts\activate.bat
python -c "import fastapi; print('✅ FastAPI instalado')"
if errorlevel 1 (
    echo ❌ Dependencias Python faltando
    echo Executando: pip install -r requirements.txt
    pip install -r requirements.txt
)
cd ..
echo.

echo [4/4] Testando Frontend...
cd frontend-solid
if not exist "node_modules\" (
    echo ⚠️ node_modules nao encontrado
    echo Executando: npm install
    npm install
) else (
    echo ✅ node_modules OK
)
cd ..
echo.

echo ========================================
echo TESTE CONCLUIDO!
echo ========================================
echo.
echo Ambiente pronto para uso!
echo Execute: start-local.bat
echo.
pause
