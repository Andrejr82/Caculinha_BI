# Checklist de Operação - Playground BI

## Pré-produção
- [ ] `PLAYGROUND_MODE` definido conforme estratégia atual.
- [ ] `PLAYGROUND_CANARY_ENABLED` revisado.
- [ ] Usuários canário configurados no Admin.
- [ ] Permissões SQL completo revisadas e com expiração quando necessário.
- [ ] Build frontend e testes backend verdes.

## Operação diária
- [ ] Verificar métricas do Playground (`/api/v1/playground/metrics`).
- [ ] Revisar feedback útil/inútil.
- [ ] Revisar auditoria de alterações de permissão (SQL e Canário).
- [ ] Confirmar que volume remoto está dentro do esperado.

## Governança e segurança
- [ ] Garantir princípio do menor privilégio para SQL completo.
- [ ] Revogar acessos temporários expirados.
- [ ] Validar que usuários fora do canário estão em rota local.
- [ ] Manter logs/auditoria habilitados.

## Rollback drill (semanal/quinzenal)
- [ ] Simular troca para `local_only`.
- [ ] Validar recuperação sem erro visual no Playground.
- [ ] Confirmar que admin consegue revogar permissões em massa.
- [ ] Registrar resultado do teste de rollback.
