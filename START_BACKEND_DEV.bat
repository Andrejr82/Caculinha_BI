@echo off
setlocal
chcp 65001 >nul

REM ------------------------------------------------------------
REM Backend local with auto-reload (manual tuning points below)
REM ------------------------------------------------------------
REM [INFO] Este script sobe SOMENTE o backend.
REM       Nao existe etapa de "esperar backend e depois subir frontend" aqui.
REM       Essa logica fica no START_SYSTEM_V2026.bat + scripts/wait_for_backend.py.
echo [BACKEND] Iniciando com hot reload...

REM [AJUSTE] Root do projeto para imports "backend.*"
set PYTHONPATH=%CD%

REM [AJUSTE] Use true para polling (mais confiavel no Windows)
REM           Troque para false se quiser priorizar menor uso de CPU.
set WATCHFILES_FORCE_POLLING=true

REM [AJUSTE] Host/porta e arquivos observados para reload
REM - --host 0.0.0.0 : acesso local/rede
REM - --port 8000    : altere se houver conflito
REM - backend.main:app: altere apenas se mudar o modulo principal da API
REM - --reload-dir   : pasta observada
REM - --reload-include: extensoes/arquivos que disparam reload
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend --reload-include *.py --reload-include .env
