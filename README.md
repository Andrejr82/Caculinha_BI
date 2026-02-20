# Caculinha BI Agent Platform v2.0

Plataforma de Business Intelligence conversacional para varejo, com backend FastAPI, frontend SolidJS e integração LLM.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Visao Geral

- Consultas em linguagem natural sobre dados de vendas/estoque.
- API com suporte a `/api/v1` e `/api/v2`.
- LLM configuravel por `.env` (padrao atual: Groq).
- Auth e perfis com Supabase (quando habilitado).
- Fallback para Parquet quando SQL Server nao esta ativo.

## Quick Start (Windows)

### Pre-requisitos

- Python 3.11+
- Node.js 18+
- Arquivo `backend/.env` configurado

### Subida recomendada

```bat
START_SYSTEM_V2026.bat
```

Esse script inicia:

- Backend FastAPI em `http://localhost:8000`
- Frontend SolidJS em `http://localhost:3000`

## Execucao Manual

### 1. Backend

```powershell
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend
```

### 2. Frontend

```powershell
cd frontend-solid
npm install
npm run dev
```

## Configuracao (.env)

Arquivo principal: `backend/.env`

### LLM

- `LLM_PROVIDER=groq|google|mock`
- `LLM_FALLBACK_PROVIDERS=groq,google` (ordem de fallback)
- `LLM_MODEL_NAME=...`
- `GROQ_API_KEY=...` e `GROQ_MODEL_NAME=...` (quando `groq`)
- `GEMINI_API_KEY=...` (necessaria para recursos que ainda dependem de Gemini)

### Seguranca

- `SECRET_KEY` (minimo 32 caracteres)
- `JWT_SECRET` (compatibilidade legada)

### Supabase

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `USE_SUPABASE_AUTH=true|false`

### Dados

- `DATABASE_URL` e `USE_SQL_SERVER=true|false`
- `PARQUET_DATA_PATH` / `PARQUET_FILE_PATH`

## API

### Endpoints base

- `GET /` status e metadados da API
- `GET /ping`
- `GET /health`
- `GET /docs`

### Prefixos

### ChatBI (v1)

- `POST /api/v1/chat/stream-token`
- `GET /api/v1/chat/stream`
- `GET /api/v1/chat/llm/status`

- `v1`: ` /api/v1/...`
- `v2`: ` /api/v2/...` (camada de compatibilidade que reaproveita routers da v1)

## Testes

Configuracao em `pytest.ini` com `testpaths = backend/tests`.

```powershell
pytest backend/tests -q
```

## Estrutura do Projeto

```text
backend/
  main.py
  app/
    api/
      middleware/
      v1/
      v2/
    config/
    core/
    services/
frontend-solid/
docs/
scripts/
START_SYSTEM_V2026.bat
```

## Observacoes

- O projeto possui partes novas e legadas convivendo.
- Nem todos os modulos usam o provider LLM de forma 100% uniforme.
- Para operacao estavel, mantenha `.env` alinhado com o fluxo que sera usado em producao.

## Licenca

MIT. Veja `LICENSE`.
