# ChatBI Go-Live - Registro de Execucao

## Janela de liberacao
- Data:
- Inicio:
- Fim:
- Ambiente:
- Versao/Tag:
- Responsavel tecnico:
- Responsavel operacao:

## Gate antes da abertura
- [ ] CI bloqueante aprovado.
- [ ] `scripts/chatbi_pre_producao_checklist.ps1` aprovado.
- [ ] UAT assinado anexado.
- [ ] `scripts/chatbi_canary_rollback_drill.ps1` executado.
- [ ] Pacote de evidencias gerado por `scripts/chatbi_release_evidence_pack.ps1`.

## Rollout canario
- Canary habilitado:
- Roles liberadas:
- Usuarios liberados:
- Horario de ativacao:
- Evidencia `403` fora do canary:
- Evidencia `200` no piloto:

## Monitoramento reforcado
| Momento | Endpoint/Painel | Resultado | Observacao |
|---|---|---|---|
| T0 | `/api/v1/admin/dashboard/chat-slo` |  |  |
| T+30m | `/api/v1/admin/dashboard/chat-slo` |  |  |
| T+2h | `/api/v1/admin/dashboard/chat-slo` |  |  |
| T+24h | `/api/v1/admin/dashboard/chat-slo` |  |  |

## Validacoes durante a janela
- [ ] Chat responde com texto, tabela, grafico e dashboard sem regressao.
- [ ] Historico de conversa persiste e reabre corretamente.
- [ ] Anexos, imagem e voz seguem operacionais para o grupo piloto.
- [ ] Automacoes aprovadas aparecem no historico e sem execucao fora de aprovacao.
- [ ] Sem degradacao material de `error_rate_pct`, `no_data_false_positive_pct` e p95.

## Rollback
- [ ] Nao foi necessario rollback.
- [ ] Rollback de acesso executado.
- [ ] Rollback de release executado.

### Caso rollback
- Motivo:
- Horario:
- Acao tomada:
- Evidencia:
- RCA preliminar:

## Decisao final
- [ ] Expandir canary.
- [ ] Manter escopo piloto.
- [ ] Bloquear expansao e corrigir antes de nova janela.

## Assinaturas
- Tecnica:
- Operacao:
- Negocio:
- Data:
