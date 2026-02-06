@echo off
echo ==========================================
echo      RESETANDO CREDENCIAIS DE ADMIN
echo ==========================================
echo.

cd /d "%~dp0"
call .venv\Scripts\activate.bat

echo Gerando novo arquivo users.parquet...
python create_users.py

echo.
echo ==========================================
echo           LOGIN RESTAURADO
echo ==========================================
echo.
echo Use estas credenciais:
echo.
echo   Usuario: admin
echo   Senha:   Admin@2024
echo.
echo ==========================================
echo IMPORTANTE:
echo Se o login falhar, limpe o LocalStorage:
echo 1. Pressione F12 no navegador
echo 2. Aba Application (ou Armazenamento)
echo 3. Local Storage -> Right click -> Clear
echo ==========================================
echo.
pause
