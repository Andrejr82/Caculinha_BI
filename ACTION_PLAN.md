# ACTION_PLAN

## Root Causes Ranked

### P0 - Playground 500 (`/api/v1/playground/stream`)
- **Cause:** `backend/app/core/llm_gemini_adapter.py` usa API antiga (`genai.configure`, `GenerativeModel`) enquanto runtime carrega `google.genai` (SDK nova), causando `AttributeError` e 500.
- **Impacto:** Playground indisponível; quebra fluxo crítico.

### P1 - Modelo LLM contaminado por parser de `.env`
- **Cause:** parser manual em `backend/app/config/settings.py` não remove comentário inline após valor entre aspas (`LLM_MODEL_NAME="gemini-2.5-pro"  # ...`).
- **Impacto:** `settings.LLM_MODEL_NAME` fica inválido/sujo em runtime (`/api/v1/playground/info` expõe valor incorreto).

### P1 - Contrato de erro/degradação no Playground
- **Cause:** exceções do adapter propagam para erro genérico sem degraded payload consistente.
- **Impacto:** UI recebe 500 em vez de mensagem acionável/degraded.

### P2 - Estabilidade inicial de E2E (flake em login)
- **Cause:** sincronização de startup frontend/back-end no baseline.
- **Impacto:** 1 falha intermitente no Playwright baseline.

## Mudanças Exatas (arquivo + função)

1. `backend/app/core/llm_gemini_adapter.py`
- `GeminiLLMAdapter.__init__`: detectar SDK (`google.genai`) e configurar cliente corretamente sem `genai.configure` quando indisponível.
- `GeminiLLMAdapter.get_completion`: fallback robusto para REST quando SDK incompatível, com resposta degradada para 429.
- `GeminiLLMAdapter.stream_completion`: produzir eventos de erro/degraded estáveis em vez de exceção quebrando rota.

2. `backend/app/config/settings.py`
- bloco manual env loader: sanitizar linha `.env` com remoção segura de comentário inline fora de aspas.
- garantir `LLM_MODEL_NAME` final limpo (`gemini-2.5-pro`) sem sufixos de comentário.

3. `backend/app/api/v1/endpoints/playground.py`
- `playground_stream`: capturar erros do adapter e emitir evento SSE de degraded/erro acionável, evitando 500 para falhas de quota/SDK.

4. `backend/tests/integration/test_stabilization_local.py` (ou arquivo de regressão equivalente)
- adicionar/ajustar caso para garantir degraded mode no playground sob falha de adapter/429.

## Risks + Local Rollback
- **Risco:** alterar adapter pode impactar chat/insights.
- **Mitigação:** mudanças mínimas e condicionais (somente caminho incompatível com SDK atual).
- **Rollback local:** restaurar os 3 arquivos citados para estado anterior via diff local (sem push).

## Prova de Correção
- Manual HTTP:
  - `/api/v1/auth/me` -> 200
  - `/api/v1/chat/stream?...&token=...` -> 200 SSE
  - `/api/v1/code-chat/stream?...&token=...` -> 200 SSE com sucesso ou erro acionável
  - `/api/v1/playground/stream` -> **não 500**; retorna stream com token/degraded em erro de quota
  - `/api/v1/playground/info` -> `model == gemini-2.5-pro`
- Testes:
  - `pytest -q`
  - `cd frontend-solid && npx playwright test`

## Manual Verification Checklist
- Login abre normalmente.
- Chat envia mensagem sem travar.
- CodeChat não quebra tela; se índice ausente, mensagem acionável exibida.
- Playground não retorna 500; em quota/erro mostra degraded.
- Nenhum token/segredo em logs de erro de frontend.
