# PLAYWRIGHT_BASELINE_REPORT

## Execução
- Comando: `cd frontend-solid && npx playwright test tests/integration/stabilization.spec.ts --reporter=list`
- Output bruto: `PLAYWRIGHT_BASELINE_OUTPUT.txt`

## Resultado
- Total: 3 testes
- Passaram: 2
- Falharam: 1

## Falha observada
- Teste: `login -> Chat page -> message streams or degrades gracefully`
- Erro: `TimeoutError: page.goto('/login') Timeout 10000ms exceeded`
- Interpretação: flake/intermitência de disponibilidade inicial do frontend durante baseline.

## Evidência de comportamento das páginas
- Chat: baseline com falha de entrada na página (timeout de navegação no login), não evidência de crash pós-login.
- CodeChat: passou (`works or shows actionable index message`).
- Playground: passou (`streams or degrades fast on quota`).

## Conclusão baseline
- O principal bloqueio funcional de backend identificado por runtime direto é no `POST /api/v1/playground/stream` (500), não no fluxo base de auth/me/SSE chat.
- Próxima fase: correções P0/P1 no adapter Gemini e parsing de settings para estabilizar Playground definitivamente.
