@echo off
setlocal EnableDelayedExpansion

echo ============================================================================
echo   BI SOLUTION - SETUP NATIVO (FASE FINAL)
echo ============================================================================
echo.

REM 1. Limpeza de Segurança
if exist backend\.venv (
    echo Removendo ambiente virtual antigo para garantir limpeza...
    rmdir /s /q backend\.venv
)

REM 2. Criar ambiente virtual novo
echo Criando novo ambiente Python...
cd backend
python -m venv .venv
if %errorlevel% neq 0 goto ERROR
echo [OK] Ambiente criado.

REM 3. Instalar dependencias
echo Ativando ambiente e instalando pacotes...
call .venv\Scripts\activate
python -m pip install --upgrade pip

echo Instalando bibliotecas (Usando binarios leves)...
REM --prefer-binary evita compilar codigo C++ lento
pip install --no-cache-dir --prefer-binary -r requirements.txt
if %errorlevel% neq 0 goto ERROR

cd ..

REM 4. Frontend
echo.
echo ============================================================================
echo   2. CONFIGURANDO FRONTEND
echo ============================================================================
echo.
cd frontend-solid
echo Instalando Node modules...
call npm install
if %errorlevel% neq 0 goto ERROR

cd ..

echo.
echo ============================================================================
echo   TUDO PRONTO! 
echo ============================================================================
echo.
echo 1. O sistema agora roda direto no seu Windows (mais rapido).
echo 2. Execute o arquivo 'start.bat' para iniciar.
echo.
pause
exit /b 0

:ERROR
echo.
echo ########################################################
echo   ERRO DETECTADO! Verifique as mensagens acima.
echo ########################################################
pause
exit /b 1
