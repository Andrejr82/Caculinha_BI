# Changelog

Todas as mudanças relevantes deste repositório serão documentadas aqui.

## [2026-02-27]

### Added
- Implementação da Fase 3 do ChatBI com pacote de hardening, observabilidade e regressão LLMOps.
- Novos runbooks e playbooks em `docs/`:
  - `docs/CHATBI_CONTEXT7_RUNBOOK.md`
  - `docs/CHATBI_FASE3_RUNBOOK_CANARY_ROLLBACK.md`
  - `docs/CHATBI_PRECISION_PLAYBOOK.md`
  - `docs/CHATBI_TEST_CASES.md`
  - `docs/CHATBI_TOOL_CONTRACTS.md`
- Novas suítes de teste para ChatBI (roteamento de tools, formatação executiva, sanitização de resposta, pesquisas de mercado e contratos de fase 3).
- Script de regressão LLMOps:
  - `backend/scripts/run_llmops_regression.py`

### Changed
- ChatBI reforçado para menor privilégio:
  - role `user` mapeada para escopo `viewer` no serviço de chat.
  - Sanitização por perfil em respostas para evitar exposição de detalhes internos para perfis restritos.
- Roteamento de pesquisa de mercado ajustado:
  - consultas genéricas priorizam cobertura multi-concorrente.
  - caminho de mercado web mantido para casos explícitos de Mercado Livre.
- Frontend consolidado para Bun:
  - lockfile oficial `frontend-solid/bun.lock`.
  - remoção de lockfiles de npm/pnpm.
  - atualização de bundle e páginas de chat/admin.

### Fixed
- Correção de regressão no roteamento de “pesquisa de mercado” que estava desviando para ferramenta menos adequada em cenário genérico.
- Melhoria de proteção contra vazamento de dados internos em blocos executivos (`Tabela operacional`, `SQL/Python`, evidências sensíveis) para perfis não privilegiados.

### Tests
- Execução validada de baterias de backend (incluindo integração de chat e roteamento competitivo):
  - Resultado consolidado principal: `79 passed, 2 skipped`.
- Testes focados de role mapping e sanitização:
  - Resultado: `16 passed`.
- Build frontend com Bun validado:
  - `bun run --cwd frontend-solid build`.

### Commits relacionados
- `a31a4e0c` chore(frontend): migrate lockfiles to bun and refresh chat/admin UI bundles
- `47d24641` feat(chatbi): implement phase 3 hardening, routing, observability and llmops regression pack
- `e92c411f` hardening: enforce least-privilege chat role and sanitize restricted outputs
- `000704dc` feat(chatbi): default to groq and add chat observability/slo dashboard
- `5ec32dfc` chore(frontend): stop tracking frontend-solid/node_modules for bun workflow
- `18dfde1f` chore: migrate frontend runtime/tooling from Node.js to Bun
