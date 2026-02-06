@echo off
echo ============================================================================
echo   LIMPEZA CONSERVADORA - BI SOLUTION (Opcao 2)
echo ============================================================================
echo.
echo Este script ira excluir:
echo   - Arquivos de log (.log)
echo   - Arquivos de backup (.backup)
echo   - Sessoes de teste (test-*.json, cache-test-*.json)
echo   - CSVs temporarios (*_temp_test.csv)
echo.
echo SEGURANCA:
echo   - Backup automatico antes de qualquer exclusao
echo   - Preview detalhado do que sera excluido
echo   - Confirmacao obrigatoria antes de executar
echo   - Relatorio completo gerado
echo   - Possibilidade de reverter (undo)
echo.
echo ============================================================================
echo.

REM Verifica se Python esta disponivel
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Por favor, instale Python 3.8+ e tente novamente.
    pause
    exit /b 1
)

set /p escolha="Deseja ver um PREVIEW primeiro? (S/N): "

if /i "%escolha%"=="S" (
    echo.
    echo ============================================================================
    echo   MODO PREVIEW - Nenhum arquivo sera excluido
    echo ============================================================================
    echo.
    python cleanup_conservative.py --dry-run
    echo.
    echo ============================================================================
    echo.
    set /p executar="Deseja executar a limpeza de verdade agora? (S/N): "
    if /i "%executar%"=="N" (
        echo.
        echo Operacao cancelada.
        pause
        exit /b 0
    )
)

echo.
echo ============================================================================
echo   EXECUTANDO LIMPEZA
echo ============================================================================
echo.

python cleanup_conservative.py

if errorlevel 1 (
    echo.
    echo ERRO durante a execucao!
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo   LIMPEZA CONCLUIDA!
echo ============================================================================
echo.
echo Para reverter a limpeza, execute:
echo    restore.bat
echo.
pause
