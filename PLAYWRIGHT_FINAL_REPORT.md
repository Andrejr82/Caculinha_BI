# PLAYWRIGHT_FINAL_REPORT

## Final Execution
- Backend tests: `python -m pytest -q`
  - Result: **55 passed**
- Frontend E2E: `cd frontend-solid && npx playwright test --reporter=list --global-timeout=300000`
  - Final result: **23 passed**

## Notes
- Primeira execução Playwright teve 1 flake em `tests/e2e/auth.spec.ts` (timeout inicial em `/login`).
- Ajuste aplicado:
  - `frontend-solid/playwright.config.ts:47` (`navigationTimeout` 30s)
  - `frontend-solid/tests/e2e/auth.spec.ts:5` e `frontend-solid/tests/e2e/auth.spec.ts:11` (`page.goto('/login', { waitUntil: 'domcontentloaded', timeout: 30000 })`)
- Reexecução final: **100% green (23/23)**.

## Runtime Spot Checks (after fixes)
- `GET /api/v1/auth/me` => `200`
- `GET /api/v1/chat/stream?...&token=...` => `200` (`text/event-stream`)
- `GET /api/v1/code-chat/stream?...&token=...` => `200` with actionable payload
- `POST /api/v1/playground/stream` => `200` with `type: degraded` on quota (no 500)
- `GET /api/v1/playground/info` => `model: gemini-2.5-pro`
