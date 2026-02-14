# Runbook Playground BI (Local-First)

## 1. Objetivo
Garantir operação segura do Playground BI com prioridade para modo econômico (`local_only`) e rollback rápido em incidentes.

## 2. Modos de operação
- `local_only`: sem LLM remota.
- `hybrid_optional`: remota opcional, controlada por canário.
- `remote_required`: remota obrigatória para quem estiver no canário.

## 3. Controles de segurança
- Flag global: `PLAYGROUND_MODE`.
- Flag de canário: `PLAYGROUND_CANARY_ENABLED`.
- Escopo de canário:
  - `PLAYGROUND_CANARY_ALLOWED_ROLES`
  - `PLAYGROUND_CANARY_ALLOWED_USERS`
- Override por usuário (Admin): permissões `playground_canary_access`.
- SQL completo separado por usuário: `playground_sql_full_access`.

## 4. Procedimento de canário
1. Manter `PLAYGROUND_MODE=local_only` em produção enquanto custo estiver sensível.
2. Habilitar `PLAYGROUND_CANARY_ENABLED=true` quando iniciar piloto remoto.
3. No Admin, liberar `Canário LLM` apenas para usuários-alvo.
4. Monitorar `/api/v1/playground/metrics` (erros, feedback útil, proporção local/remoto).
5. Expandir gradualmente.

## 5. Resposta a incidente
### Sintomas críticos
- Aumento de erro no Playground.
- Latência alta persistente.
- Resposta insegura/inadequada.
- Custo remoto acima do limite esperado.

### Ação imediata (rollback)
1. Definir `PLAYGROUND_MODE=local_only`.
2. Opcional: `PLAYGROUND_CANARY_ENABLED=false`.
3. No Admin:
   - Revogar `Canário LLM de Todos`.
   - Revogar `SQL de Todos` se incidente envolver risco de consulta.
4. Validar endpoint `/api/v1/playground/info`:
   - `remote_llm_enabled=false`.
5. Registrar incidente em auditoria e pós-mortem.

## 6. Checklist de validação pós-rollback
- Playground responde sem erro visual.
- Rotas `rule/template/local_fallback` funcionando.
- Fluxo de feedback permanece operacional.
- Export CSV/JSON funcionando.
- Admin continua gerenciando permissões normalmente.

## 7. Critério de retorno ao rollout
- Incidente identificado e corrigido.
- Testes de regressão executados.
- Métricas estabilizadas por janela mínima acordada.
