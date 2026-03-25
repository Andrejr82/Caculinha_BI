# ADR-004: RBAC Orientado a Capacidade

## Status
Accepted

## Contexto
O ChatBI executa múltiplas capacidades (consulta interna, mercado, cálculo, dashboard) com risco diferente por perfil de usuário.

## Decisão
Aplicar escopo de capacidades por role no fluxo do chat:
- seleção de tools por perfil (`admin`, `analyst`, `viewer`, `guest`);
- rate-limit por perfil/usuário;
- sanitização de saída para perfis restritos.

## Consequências
- Positivas: menor risco de vazamento, melhor governança e previsibilidade.
- Negativas: maior complexidade de manutenção de políticas de perfil.
- Mitigação: testes de contrato por role e auditoria estruturada por `request_id`.
