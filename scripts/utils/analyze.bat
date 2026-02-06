@echo off
echo ============================================
echo Analise Profunda do Projeto BI_Solution
echo ============================================
echo.

REM Verifica se Python esta disponivel
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Por favor, instale Python 3.8+ e tente novamente.
    pause
    exit /b 1
)

echo Executando analise...
echo Isso pode levar alguns minutos dependendo do tamanho do projeto.
echo.

python analyze_project_detailed.py

if errorlevel 1 (
    echo.
    echo ERRO durante a execucao!
    pause
    exit /b 1
)

echo.
echo ============================================
echo Analise concluida com sucesso!
echo ============================================
echo.
echo Os seguintes arquivos foram gerados:
echo   - ANALISE_PROJETO_DETALHADA.md (relatorio completo com descricao de cada arquivo)
echo   - analise_projeto_detalhada.json (dados detalhados em JSON)
echo.
echo Compartilhe o arquivo ANALISE_PROJETO_DETALHADA.md para revisao.
echo.
pause
