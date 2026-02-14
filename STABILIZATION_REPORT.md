# STABILIZATION_REPORT

## What was broken
1. `Playground` retornava `500` em `/api/v1/playground/stream` por incompatibilidade do SDK Gemini (`google.genai` sem `configure`).
2. `LLM_MODEL_NAME` em runtime estava contaminado por comentário inline da `.env`.
3. Suite Playwright tinha flake de bootstrap no smoke de login (`/login` timeout curto).

## What was fixed
1. SDK compatibility + fallback (definitivo)
- File: `backend/app/core/llm_gemini_adapter.py:53`
  - Detecta modo SDK (`legacy` vs `new`) e evita `genai.configure` no caminho incompatível.
- File: `backend/app/core/llm_gemini_adapter.py:172`
  - `stream_completion` usa fallback REST no SDK novo.
- File: `backend/app/core/llm_gemini_adapter.py:268`
  - `get_completion` usa fallback REST no SDK novo.

2. Robust `.env` parsing (modelo canônico limpo)
- File: `backend/app/config/settings.py:244`
  - Remove comentário inline fora de aspas e limpa valor com quotes corretos.
- Resultado: `settings.LLM_MODEL_NAME == gemini-2.5-pro` em runtime (`/api/v1/playground/info`).

3. Playground degraded mode (sem 500)
- File: `backend/app/api/v1/endpoints/playground.py:41`
  - Inicialização do adapter movida para dentro do gerador SSE para evitar hard-fail HTTP 500.
- File: `backend/app/api/v1/endpoints/playground.py:101`
  - Em quota/rate-limit, retorna evento `degraded` acionável.
- File: `backend/app/api/v1/endpoints/playground.py:117`
  - Sempre fecha stream com `done` em erro.

4. Regressão E2E (flake login)
- File: `frontend-solid/playwright.config.ts:47`
  - `navigationTimeout` aumentado para 30s.
- File: `frontend-solid/tests/e2e/auth.spec.ts:5`
- File: `frontend-solid/tests/e2e/auth.spec.ts:11`
  - Navegação para `/login` com timeout robusto e `domcontentloaded`.

5. Teste de regressão backend adicionado
- File: `backend/tests/integration/test_stabilization_local.py`
  - `test_playground_stream_degrades_instead_of_500` garante que falha de adapter não vira 500.

## Evidence (commands and outcomes)
- `python -m pytest -q` => **55 passed**
- `cd frontend-solid && npx playwright test --reporter=list --global-timeout=300000` => **23 passed**
- Runtime checks:
  - `GET /api/v1/auth/me` => `200`
  - `GET /api/v1/chat/stream?...&token=...` => `200` SSE
  - `GET /api/v1/code-chat/stream?...&token=...` => `200` (mensagem acionável sem crash)
  - `POST /api/v1/playground/stream` => `200` com `degraded` em quota
  - `GET /api/v1/playground/info` => `{"model":"gemini-2.5-pro", ...}`

## Remaining items
- Nenhum bloqueador crítico restante para os critérios definidos.
- `CodeChat` ainda depende da inicialização/índice do serviço para resposta completa, mas já degrada com mensagem acionável sem quebrar a UI.

## How to reproduce success
1. Inicie backend e frontend localmente.
2. Execute `python -m pytest -q`.
3. Execute `cd frontend-solid && npx playwright test --reporter=list --global-timeout=300000`.
4. Valide endpoints:
   - `/api/v1/auth/me`
   - `/api/v1/chat/stream`
   - `/api/v1/code-chat/stream`
   - `/api/v1/playground/stream`
   - `/api/v1/playground/info`
