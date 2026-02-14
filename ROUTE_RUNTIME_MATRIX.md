# ROUTE_RUNTIME_MATRIX

| Page | Endpoint | Method | Auth mode | Status | Backend route exists? | Observation |
|---|---|---|---|---|---|---|
| Chat.tsx | `/api/v1/chat/stream` | GET (SSE) | Query token (`?token=`) | OK (200) | Yes | EventSource flow funcional com token na query. |
| Chat.tsx | `/api/v1/chat/stream` | GET (SSE) | Bearer header | OK (200) | Yes | Compatível também com header auth. |
| Chat.tsx | `/api/v1/chat/stream` | GET (SSE) | Sem token | FAIL (401 esperado) | Yes | Retorna JSON estruturado: `Missing authentication token`. |
| CodeChat.tsx | `/api/v1/code-chat/stream` | GET (SSE) | Query token (`?token=`) | PARTIAL (200 + erro funcional) | Yes | Retorna evento de erro acionável (`Service not initialized`). Sem crash HTTP. |
| Playground.tsx | `/api/v1/playground/stream` | POST (SSE payload) | Bearer header | FAIL (500) | Yes | Erro runtime no adapter Gemini (`google.genai` incompatível). |
| Playground.tsx | `/api/v1/playground/info` | GET | Bearer header | OK (200) | Yes | Campo `model` contaminado por comentário inline de `.env`. |
| Insights (supporting) | `/api/v1/insights/proactive` | GET | Bearer header | OK (200 degraded) | Yes | Degraded mode por quota 429 já existe no endpoint. |
| Alias check | `/api/v2/auth/me` | GET | Bearer header | OK (200) | Yes | Paridade básica v2->v1 confirmada em runtime. |
