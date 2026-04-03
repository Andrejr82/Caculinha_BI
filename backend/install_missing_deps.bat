@echo off
setlocal
REM ============================================================================
REM Sincronizar dependencias do backend
REM Fonte canonica:
REM   - requirements.in -> requirements.txt (base)
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

echo [1/4] Verificando ambiente virtual...
if not exist ".venv\\Scripts\\python.exe" (
    echo Criando ambiente virtual em backend\\.venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo ERRO: Falha ao criar ambiente virtual.
        pause
        exit /b 1
    )
)

echo.
echo [2/4] Atualizando pip...
".venv\\Scripts\\python.exe" -m pip install --upgrade pip

if errorlevel 1 (
    echo.
    echo ERRO: Falha ao atualizar pip.
    pause
    exit /b 1
)

echo.
echo [3/4] Instalando dependencias base...
echo   - backend\\requirements.txt
echo.

".venv\\Scripts\\python.exe" -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERRO: Falha ao instalar requirements.txt
    pause
    exit /b 1
)

echo.
echo [4/5] Verificando instalacao...
echo.

".venv\\Scripts\\python.exe" -c "import importlib; pkgs = ['plotly', 'kaleido', 'matplotlib', 'seaborn', 'langchain_google_genai']; installed = []; missing = []; [installed.append(p) if importlib.import_module(p) or True else None for p in pkgs]; print(f'Instalados: {len(installed)}/{len(pkgs)}'); [print(f'  OK: {p}') for p in installed]"

if errorlevel 1 (
    echo.
    echo AVISO: Alguns pacotes podem nao ter sido instalados corretamente.
    echo Execute manualmente:
    echo   .venv\\Scripts\\python.exe -m pip install -r requirements.txt
)

echo.
echo [5/5] Preparando cache local do modelo de embeddings...
echo.
".venv\\Scripts\\python.exe" scripts\\maintenance\\preload_embedding_model.py --allow-download

if errorlevel 1 (
    echo.
    echo AVISO: Nao foi possivel pre-carregar o modelo de embeddings.
    echo O backend continuara funcional, mas pode cair em fallback deterministico ate o cache existir.
)

echo.
echo ========================================================================
echo   Instalacao Concluida!
echo ========================================================================
echo.
echo Proximos passos:
echo   1. Ativar o ambiente virtual: .venv\\Scripts\\activate
echo   2. Executar o backend: python -m uvicorn backend.main:app --reload
echo   3. Garantir em backend\\.env:
echo      RAG_EMBEDDING_LOCAL_FILES_ONLY=true
echo      RAG_EMBEDDING_PRELOAD_ON_STARTUP=true
echo   4. Testar graficos: python -c "from app.core.tools.chart_tools import chart_tools; print(f'{len(chart_tools)} ferramentas')"
echo.
pause
