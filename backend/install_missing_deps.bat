@echo off
REM ============================================================================
REM Instalar Dependências Faltantes - Agent Solution BI Backend
REM ============================================================================
REM
REM Este script instala TODAS as dependências que estão faltando no ambiente
REM virtual do projeto Agent Solution BI.
REM
REM Dependências que serão instaladas:
REM   - plotly==6.5.0       (CRÍTICO - gráficos)
REM   - kaleido==1.2.0      (IMPORTANTE - export de gráficos)
REM   - matplotlib==3.10.7  (IMPORTANTE - backend de visualização)
REM   - seaborn==0.13.2     (IMPORTANTE - gráficos estatísticos)
REM   - langchain-openai==1.0.3  (MODERADO - integração LangChain)
REM   - langchain-google-genai==2.0.5  (MODERADO - integração Gemini)
REM
REM ============================================================================

echo.
echo ========================================================================
echo   Instalacao de Dependencias Faltantes - Agent Solution BI
echo ========================================================================
echo.

cd /d "%~dp0"

REM Verificar se estamos no diretório correto
if not exist "pyproject.toml" (
    echo ERRO: pyproject.toml nao encontrado!
    echo Certifique-se de estar executando este script no diretorio backend/
    pause
    exit /b 1
)

REM Verificar se Poetry está instalado
poetry --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERRO: Poetry nao encontrado!
    echo.
    echo Instale o Poetry primeiro:
    echo   powershell -Command "(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -"
    echo.
    pause
    exit /b 1
)

echo [1/5] Verificando ambiente virtual...
if not exist ".venv" (
    echo Criando ambiente virtual...
    poetry install
)

echo.
echo [2/5] Instalando dependencias de visualizacao (CRITICO)...
echo   - plotly ^6.5.0
echo   - kaleido ^1.2.0
echo   - matplotlib ^3.10.7
echo   - seaborn ^0.13.2
echo.

poetry add plotly@^6.5.0 kaleido@^1.2.0 matplotlib@^3.10.7 seaborn@^0.13.2

if errorlevel 1 (
    echo.
    echo ERRO: Falha ao instalar dependencias de visualizacao!
    pause
    exit /b 1
)

echo.
echo [3/5] Instalando dependencias LangChain...
echo   - langchain-openai ^1.0.3
echo   - langchain-google-genai ^2.0.5
echo.

poetry add langchain-openai@^1.0.3 langchain-google-genai@^2.0.5

if errorlevel 1 (
    echo.
    echo AVISO: Falha ao instalar algumas dependencias LangChain
    echo O sistema pode funcionar parcialmente.
)

echo.
echo [4/5] Sincronizando ambiente...
poetry install --sync

echo.
echo [5/5] Verificando instalacao...
echo.

poetry run python -c "import sys; sys.stdout.reconfigure(encoding='utf-8'); pkgs = ['plotly', 'kaleido', 'matplotlib', 'seaborn', 'langchain_openai']; installed = []; missing = []; [installed.append(p) if __import__(p) or True else missing.append(p) for p in pkgs]; print(f'Instalados: {len(installed)}/{len(pkgs)}'); [print(f'  OK: {p}') for p in installed]; [print(f'  MISS: {p}') for p in missing] if missing else None"

if errorlevel 1 (
    echo.
    echo AVISO: Alguns pacotes podem nao ter sido instalados corretamente.
    echo Execute manualmente: poetry add plotly kaleido matplotlib seaborn
)

echo.
echo ========================================================================
echo   Instalacao Concluida!
echo ========================================================================
echo.
echo Proximos passos:
echo   1. Ativar o ambiente virtual: poetry shell
echo   2. Executar o backend: python main.py
echo   3. Testar graficos: python -c "from app.core.tools.chart_tools import chart_tools; print(f'{len(chart_tools)} ferramentas')"
echo.
pause
