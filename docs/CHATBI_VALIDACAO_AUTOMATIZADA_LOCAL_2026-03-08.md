# ChatBI - Validacao Automatizada Local

## Data
- 2026-03-08

## Objetivo
- Consolidar a evidência técnica de que a stack ativa do ChatBI está implementada e funcionando no repositório local.

## Resultado geral
- Status: aprovado
- Implementação de código: concluída
- Regressões automatizadas críticas: sem falhas
- Pendências restantes: apenas homologação assinada e go-live real monitorado

## Bateria executada
- `powershell -ExecutionPolicy Bypass -File scripts/chatbi_uat_local.ps1`
- `powershell -ExecutionPolicy Bypass -File scripts/chatbi_release_evidence_pack.ps1 -RunChecklist -SkipApiCalls`

## Resultado do UAT automatizado local
- `backend_uat_contracts`: OK
- `frontend_typecheck`: OK
- `frontend_unit_tests`: OK
- `frontend_build`: OK
- `frontend_playwright_uat`: OK
- `backend_stream_load`: OK

## Evidencias geradas
- UAT automatizado local: [summary.json](c:/Projetos_BI/Caculinha_BI/docs/uat-local/20260308_151048/summary.json)
- Logs do UAT local:
  - [backend_uat_contracts.log](c:/Projetos_BI/Caculinha_BI/docs/uat-local/20260308_151048/backend_uat_contracts.log)
  - [frontend_build.log](c:/Projetos_BI/Caculinha_BI/docs/uat-local/20260308_151048/frontend_build.log)
  - [frontend_playwright_uat.log](c:/Projetos_BI/Caculinha_BI/docs/uat-local/20260308_151048/frontend_playwright_uat.log)
- Pacote de release/evidências: [manifest.json](c:/Projetos_BI/Caculinha_BI/docs/release-evidence/20260308_152427/manifest.json)
- Checklist integrado anexado ao pacote: [pre_producao_checklist.log](c:/Projetos_BI/Caculinha_BI/docs/release-evidence/20260308_152427/pre_producao_checklist.log)

## Cobertura validada
- Chat com texto, gráfico, tabela, dashboard, memória, citações e confiança.
- Follow-ups contextuais de BI e mercado.
- Uploads, multimodalidade e saída por voz.
- Automações com aprovação e auditoria.
- Hardening, capability gating, canary/rollback drill e carga controlada.
- Playground e Playground Lab em funcionamento.

## O que ainda depende de ambiente real
- Executar o UAT com usuário piloto em homologação e coletar assinaturas em [CHATBI_UAT_EXECUCAO_HOMOLOG_TEMPLATE.md](c:/Projetos_BI/Caculinha_BI/docs/CHATBI_UAT_EXECUCAO_HOMOLOG_TEMPLATE.md).
- Executar o go-live controlado e registrar a janela em [CHATBI_GO_LIVE_EXECUCAO_TEMPLATE.md](c:/Projetos_BI/Caculinha_BI/docs/CHATBI_GO_LIVE_EXECUCAO_TEMPLATE.md).
- Coletar as evidências reais de `403/200` do canary e os endpoints operacionais com token via [chatbi_release_evidence_pack.ps1](c:/Projetos_BI/Caculinha_BI/scripts/chatbi_release_evidence_pack.ps1).
