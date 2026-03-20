# ChatBI Fase 8 - Checklist Integrado de Pre-Producao

## Objetivo
Executar uma validacao unica e rastreavel antes do go-live, cobrindo frontend, backend, observabilidade, seguranca e automacoes da stack ativa.

## Execucao recomendada
- `powershell -ExecutionPolicy Bypass -File scripts/chatbi_pre_producao_checklist.ps1`
- `powershell -ExecutionPolicy Bypass -File scripts/chatbi_pre_producao_checklist.ps1 -RunLoad`

## Checklist operacional

### Frontend
- [ ] `npx tsc --noEmit -p frontend-solid/tsconfig.json` sem erros.
- [ ] `npx vite build` em `frontend-solid/` concluido.
- [ ] Chat renderiza texto, tabela, grafico, dashboard, imagem, audio e automacao sem colisoes visuais.

### Backend e contrato
- [ ] `backend/tests/integration/test_chat_endpoint.py` aprovado.
- [ ] `backend/tests/integration/test_chat_history_endpoint.py` aprovado.
- [ ] `backend/tests/integration/test_memory_endpoint.py` aprovado.
- [ ] `backend/tests/integration/test_ingest_endpoint.py` aprovado.
- [ ] `backend/tests/test_chat_service_memory_rag.py` e `backend/tests/test_chat_service_document_rag.py` aprovados.
- [ ] `backend/tests/test_chat_automation_service.py` aprovado.

### Observabilidade, seguranca e gates
- [ ] `backend/tests/test_chat_service_observability.py` aprovado.
- [ ] `backend/tests/test_content_safety.py` aprovado.
- [ ] `backend/tests/test_admin_dashboard_chat_slo.py` aprovado.
- [ ] `backend/tests/llmops/test_domain_eval_gate.py` aprovado.
- [ ] `backend/tests/llmops/test_capability_targets.py` aprovado.

### Canary, rollback e carga
- [ ] `scripts/chatbi_canary_rollback_drill.ps1` executado.
- [ ] `backend/tests/integration/test_chat_stream_load.py` aprovado para concorrencia controlada e p95 estavel.
- [ ] `backend/tests/load/test_chat_stream_homologation.py` executado em homologacao com `RUN_LOAD_TESTS=1`.
- [ ] Evidencias de `403` fora do canary e `200` no piloto anexadas ao pacote de release.

## Evidencias minimas
- Print ou log do checklist executavel.
- Resultado do endpoint `GET /api/v1/admin/dashboard/chat-slo`.
- Payload do `GET /api/v1/chat/capabilities?debug=true` para o perfil piloto.
- Historico de automacoes em `GET /api/v1/chat/automation/history`.
- Pacote consolidado gerado por `scripts/chatbi_release_evidence_pack.ps1`.

## Regra de bloqueio
- Qualquer item critico em aberto bloqueia go-live.
- Bloqueadores devem ser registrados com owner, prazo e decisao de rollback ou correcao.
