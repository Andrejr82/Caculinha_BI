# ChatBI Sprint 6 - Go-Live Controlado

## Objetivo
Executar liberacao com quality gate bloqueante, rollout canario e rollback operavel com evidencias.

## 1) Gate bloqueante de release (CI)
- Workflow: `.github/workflows/ci.yml`
- Condicao minima:
  - `scripts/sprint0_quality_gate.ps1 -Mode gate` aprovado.
  - Suite de testes backend aprovada.
  - Gate de dominio aprovado: `backend/tests/llmops/test_domain_eval_gate.py`.
  - Build frontend aprovado.

## 2) Pre-check local antes do canario
1. Executar:
  - `powershell -ExecutionPolicy Bypass -File scripts/chatbi_pre_producao_checklist.ps1`
2. Validar UAT:
  - `docs/CHATBI_UAT_CENARIOS_NEGOCIO.md`
  - Consolidar assinatura em `docs/CHATBI_UAT_EXECUCAO_HOMOLOG_TEMPLATE.md`
3. Revisar contrato e suporte:
  - `docs/CHATBI_CONTRATO_FINAL_E_SUPORTE.md`
4. Executar checklist legado/complementar:
   - `powershell -ExecutionPolicy Bypass -File scripts/chatbi_phase3_checklist.ps1`
5. Executar drill:
   - `powershell -ExecutionPolicy Bypass -File scripts/chatbi_canary_rollback_drill.ps1`
6. Revisar matriz de capacidades:
   - `docs/CHATBI_CAPABILITY_ROLLOUT_RUNBOOK.md`
7. Gerar pacote de evidencias:
   - `powershell -ExecutionPolicy Bypass -File scripts/chatbi_release_evidence_pack.ps1 -RunChecklist -Token <TOKEN>`

## 3) Rollout canario
1. Habilitar canario:
   - `CHAT_CANARY_ENABLED=true`
2. Definir escopo inicial (recomendado):
   - `CHAT_CANARY_ALLOWED_ROLES=admin`
   - `CHAT_CANARY_ALLOWED_USERS=usuario.teste`
3. Validar acesso:
   - Usuario fora do escopo recebe `403` em `/api/v1/chat/stream-token`.
   - Usuario no escopo recebe `200` em `/api/v1/chat/stream-token`.
4. Janela de observacao:
   - 24 horas com monitoramento em `/api/v1/admin/dashboard/chat-slo`.

## 4) Criterios de expansao do canario
- `slo_status=healthy` no periodo.
- Sem aumento relevante em:
  - `error_rate_pct`
  - `no_data_false_positive_pct`
  - latencia p95 complexa.
- Feedback util sem regressao.
- Historico de automacoes sem falhas ou execucoes fora de aprovacao:
  - `GET /api/v1/chat/automation/history`

## 5) Rollback
1. Rollback de acesso imediato:
   - `CHAT_CANARY_ENABLED=false` (liberacao total) ou ajuste da allowlist.
2. Rollback de release:
   - Reimplantar ultima tag estavel.
3. Pos-rollback:
   - Reexecutar `scripts/chatbi_phase3_checklist.ps1`.
   - Registrar incidente e causa raiz.

## 6) Evidencias minimas
- Log/print do gate de CI.
- Log/print do `scripts/chatbi_pre_producao_checklist.ps1`.
- UAT assinado em `docs/CHATBI_UAT_CENARIOS_NEGOCIO.md`.
- Registro formal de homologacao em `docs/CHATBI_UAT_EXECUCAO_HOMOLOG_TEMPLATE.md`.
- Registro da janela de liberacao em `docs/CHATBI_GO_LIVE_EXECUCAO_TEMPLATE.md`.
- Evidencia de bloqueio canario (`403`) para usuario fora do escopo.
- Evidencia de acesso permitido (`200`) para usuario no escopo.
- Evidencia de rollback testado.
