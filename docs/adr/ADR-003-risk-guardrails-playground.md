# ADR-003: Guardrails de Risco e Operação

## Status
Accepted

## Contexto
Playground pode gerar scripts/consultas com impacto operacional se não houver controle.

## Decisão
Aplicar guardrails obrigatórios: validação de entrada, limite de escopo, auditoria por requisição e rate limit por perfil.

## Consequências
- Positivas: redução de incidentes e melhor rastreabilidade.
- Negativas: aumento de esforço inicial de implementação.
- Mitigação: rollout incremental por sprint e métricas de adoção/erro.
