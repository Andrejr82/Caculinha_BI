# ChatBI Fase 3 - Runbook Canary e Rollback

## Objetivo
Operar o ChatBI em liberacao controlada (canary), com validacao de regressao e procedimento de rollback testavel.

## Pre-requisitos
- Variaveis de ambiente configuradas:
  - `CHAT_CANARY_ENABLED`
  - `CHAT_CANARY_ALLOWED_ROLES`
  - `CHAT_CANARY_ALLOWED_USERS`
- Dataset LLMOps versionado:
  - `backend/tests/llmops/datasets/chatbi_golden_v1.json`

## Passo 1 - Validar Fase 3 localmente
1. Executar checklist:
   - `powershell -ExecutionPolicy Bypass -File scripts/chatbi_phase3_checklist.ps1`
2. Esperado:
   - Regressao LLMOps com 100% de casos aprovados.
   - Testes de contrato Fase 3 sem falhas.

## Passo 2 - Liberacao Canary
1. Ativar canary:
   - `CHAT_CANARY_ENABLED=true`
2. Definir escopo inicial:
   - Exemplo: `CHAT_CANARY_ALLOWED_ROLES=admin`
   - Exemplo: `CHAT_CANARY_ALLOWED_USERS=usuario.teste`
3. Validar rota de templates:
   - `GET /api/v1/chat/report-templates`
4. Validar acesso:
   - Usuario fora do canary deve receber `403` em `/api/v1/chat/stream-token` e `/api/v1/chat/stream`.

## Passo 3 - Monitorar
- Acompanhar:
  - `GET /api/v1/admin/dashboard/chat-slo`
  - logs de erro do backend
  - taxa de feedback util no chat
- Janela minima recomendada:
  - 24h com grupo piloto

## Passo 4 - Expandir Canary
1. Adicionar perfis/usuarios gradualmente em `CHAT_CANARY_ALLOWED_ROLES` e `CHAT_CANARY_ALLOWED_USERS`.
2. Repetir checklist executavel antes de cada ampliacao.

## Rollback
1. Acesso imediato:
   - `CHAT_CANARY_ENABLED=false` para liberar acesso total OU
   - remover perfis/usuarios problematicos da allowlist.
2. Rollback de release:
   - Reimplantar tag anterior conhecida como estavel.
3. Pos-rollback:
   - Rodar novamente `scripts/chatbi_phase3_checklist.ps1`
   - Registrar incidente e causa raiz.

## Evidencias minimas para aprovacao TI + negocio
- Resultado do checklist executavel.
- Evidencia da regressao LLMOps.
- Evidencia de bloqueio canary (403 fora de escopo).
- Evidencia de rollback testado.
