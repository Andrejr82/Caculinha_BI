# DIAGNOSTIC_REPORT

## Phase 0 - Local Safety Snapshot
- Branch atual (`git rev-parse --abbrev-ref HEAD`): `local-stabilization-20260214`
- Snapshot de alterações locais: `_snapshot_uncommitted.diff` gerado.
- Tentativa de criar branch de segurança: `git checkout -b local-stabilization-20260214` -> já existente.

### git status --porcelain=v1 (resumo)
- Worktree com alterações extensas e não commitadas em `.agent/`, `backend/`, `frontend-solid/` e artefatos de teste.
- Estado preservado sem reset/revert.

### git log -n 30 --oneline --decorate (top)
- `400bb72c (HEAD -> local-stabilization-20260214, origin/snapshot-fix, snapshot-fix, local-stabilization-2026-02-14) chore: remove generated artifacts from git tracking ...`
- Histórico local confirma branch de estabilização já ativa.

## Phase 1 - Runtime Diagnostics (Local)

### Backend startup evidence
- Startup confirmado pelo log runtime informado pelo usuário:
  - `Uvicorn running on http://0.0.0.0:8000`
  - `Application startup complete.`
  - `request_id` presente no startup JSON (`19867ee1-22d6-49ea-93f5-aea0ffcf181d`).
- Health checks diretos:
  - `GET /health` => `200`
  - `GET /ping` => `200`
  - `GET /docs` => `200`

### Frontend startup evidence
- Frontend disponível em `localhost:3000` durante execução de Playwright baseline.

### Mandatory endpoint verification

#### 1) /api/v1/auth/me
- Requisição:
  - `POST /api/v1/auth/login` com `user@agentbi.com/user123` => `200`
  - `GET /api/v1/auth/me` com `Authorization: Bearer <token>` => `200`
- Payload observado:
  - `email: null`
  - `created_at: null`
  - `updated_at: null`
  - `allowed_segments: ["*"]`
- Conclusão: no estado local atual, o bug histórico de `500` em `/auth/me` **não reproduziu**.

#### 2) SSE query token (EventSource)
- `GET /api/v1/chat/stream?q=teste&token=...&session_id=diag-1` => `200`, `text/event-stream`
- `GET /api/v1/chat/stream?q=teste&session_id=diag-2` com bearer header => `200`, `text/event-stream`
- `GET /api/v1/chat/stream` sem token => `401`, body: `{"detail":"Missing authentication token"}`
- `GET /api/v1/code-chat/stream?q=hello&token=...` => `200`, SSE com payload de erro acionável:
  - `{"type":"error","content":"Service not initialized. Check logs."}`
- Conclusão: leitura de token via query já está ativa; sem token retorna 401 correto.

#### 3) API versioning
- `/api/v1` está canônica em `backend/app/api/v1/router.py`.
- `/api/v2` existente como camada de alias (`backend/app/api/v2/__init__.py` reusa routers v1).
- `GET /api/v2/auth/me` => `200` equivalente ao v1.

#### 4) LLM/model + 429 behavior
- `GET /api/v1/insights/proactive` => `200` com degraded payload contendo mensagem de quota `429 RESOURCE_EXHAUSTED` e instruções.
- **Falha crítica reproduzida:** `POST /api/v1/playground/stream` com payload válido (`message`, `history`, `stream`) => `500` `{"detail":"Erro de autenticação"}`.
- Evidência complementar em `auth_debug.log`:
  - `AttributeError: module 'google.genai' has no attribute 'configure'`
  - Path: `/api/v1/playground/stream`
- `GET /api/v1/playground/info` => `200`, porém `model` veio com string contaminada por comentário de `.env`:
  - `"\"gemini-2.5-pro\"  # Maximum stable capability ..."`
- Conclusão: principal bloqueio atual é incompatibilidade SDK Gemini no adapter + parsing frágil de `.env` para `LLM_MODEL_NAME`.

#### 5) Data availability + RBAC fallback
- `settings.PARQUET_DATA_PATH` => `C:\Projetos_BI\BI_Solution\backend\data\parquet\admmat.parquet`
- Exists => `True`; `ROW_COUNT` => `1113822` (>0).
- `/auth/me` devolveu `allowed_segments=["*"]` para usuário autenticado (fallback funcional no cenário testado).

## Page-by-page evidence table

| Page | Endpoint(s) | Method | Status | Error/Behavior | Probable Root Cause | Evidence |
|---|---|---|---|---|---|---|
| Chat.tsx | `/api/v1/chat/stream?q=...&token=...&session_id=...` | GET (SSE) | 200 | Stream inicia e entrega tokens | OK | direct runtime call + baseline playwright |
| CodeChat.tsx | `/api/v1/code-chat/stream?q=...&token=...` | GET (SSE) | 200 | Stream retorna erro acionável `Service not initialized` | Dependência/serviço de code index não inicializado | direct runtime call |
| Playground.tsx | `/api/v1/playground/stream` | POST (SSE) | 500 | `{"detail":"Erro de autenticação"}` | `GeminiLLMAdapter` usa `genai.configure` incompatível com SDK atual | direct runtime call + `auth_debug.log` stack |

## Playwright baseline
- Arquivo bruto: `PLAYWRIGHT_BASELINE_OUTPUT.txt`
- Resultado baseline (stabilization suite):
  - 1 failed, 2 passed.
  - Falha: timeout em `page.goto('/login')` (intermitência de disponibilidade de frontend em startup).

## Findings summary (rank)
- P0: Playground stream quebra com 500 por incompatibilidade SDK Gemini (`google.genai` sem `configure`).
- P1: `LLM_MODEL_NAME` lido com comentário inline da `.env` por parser manual, contaminando configuração de modelo.
- P1: CodeChat retorna degraded/error acionável (aceitável parcialmente), porém depende de inicialização de serviço/index.
- P2: Baseline Playwright apresentou flake de disponibilidade inicial do frontend (`/login` timeout), sem crash sistêmico nas outras duas jornadas.
