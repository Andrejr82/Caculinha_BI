# Backlog Técnico - Playground BI

## Sprint 0 - Estabilização (em andamento)
- [x] Criar plano versionado em `playground-bi-implementation-plan.md`.
- [x] Criar script de quality gate (`scripts/sprint0_quality_gate.ps1`).
- [x] Registrar ADRs iniciais (`docs/adr/ADR-001..003`).
- [ ] Fechar pendências de versionamento (workspace limpo).
- [x] Remover `continue-on-error: true` do pipeline e tornar gate bloqueante.
- [x] Feature flag de execução no Playground (`PLAYGROUND_MODE=local_only|hybrid_optional|remote_required`), default econômico `local_only`.

## Sprint 1 - Motor determinístico BI
- [x] Criar módulo `backend/app/core/playground_rules_engine.py`.
- [ ] Implementar intents iniciais:
- [x] `parquet.filter.status_error`
- [x] `sql.produtos_sem_venda`
- [x] `ruptura.loja_periodo`
- [x] `transferencias.entre_lojas`
- [x] `admat_une.checklist_operacional`
- [x] Responder com metadados (`source`, `confidence`, `intent`).
- [x] Cobrir com testes unitários.

## Sprint 2 - Catálogo e segurança de execução
- [x] Criar catálogo de prompts/intents em `backend/app/core/prompts/bi_intents_catalog.json`.
- [x] Validar saída de código SQL/Python (denylist básica).
- [x] Limitar escopo de consultas por perfil de usuário (`playground_sql_full_access`).
- [x] Incluir auditoria por request (`request_id`, `user`, `intent`, `source`, `confidence`).
- [x] Expor controles na Área de Administração (toggle por usuário, filtro, revogação em massa).
- [x] Roteador em camadas no Playground (`rule -> template -> local_fallback -> remote_optional`).
- [x] Schema de saída padronizado (`summary + table + action`) com enforcement em respostas locais.

## Sprint 3 - Qualidade e observabilidade
- [x] Métricas operacionais do Playground (`/api/v1/playground/metrics`) com requests e taxa de feedback útil.
- [x] Métricas avançadas: latência p95/p99 e taxa de erro por endpoint.
- [x] Testes de integração de ponta a ponta para `/api/v1/playground/chat` e `/api/v1/playground/stream`.
- [x] Feedback útil/inútil no Playground com persistência auditável.
- [x] Export de histórico do Playground em CSV/JSON.

## Sprint 4 - Rollout operacional BI
- [x] Feature flag por grupo de usuários.
- [x] Canário com usuários do canal físico (gerência e analistas).
- [x] Runbook de rollback e resposta a incidente.
- [x] Treinamento e checklist de operação.
