@echo off
REM Script de Execução de Testes Estáveis - Caculinha BI
REM Executa apenas a suíte de testes de contrato e pipeline (Hardening Phase)

echo ===================================================
echo  RODANDO TESTES DE ESTABILIDADE (HARDENING PHASE)
echo ===================================================

set PYTHONPATH=%CD%

echo.
echo [1/2] Testes de Contrato (DuckDB, Retriever, LLM)...
python -m pytest backend/tests/contracts/ -v
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Falha nos testes de contrato!
    exit /b %ERRORLEVEL%
)

echo.
echo [2/2] Testes de Pipeline Cognitivo (ChatService End-to-End)...
python -m pytest backend/tests/pipelines/ -v
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Falha nos testes de pipeline!
    exit /b %ERRORLEVEL%
)

echo.
echo ===================================================
echo  SUCESSO: TODOS OS TESTES ESTAVEIS PASSARAM!
echo ===================================================
exit /b 0
