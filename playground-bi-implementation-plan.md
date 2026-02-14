# Plano de Implementação - Playground BI (Robusto)

## Objetivo
Transformar o Playground em ferramenta de BI confiável para operação diária, com arquitetura híbrida (determinística + LLM opcional), observabilidade, segurança e rollout controlado.

## Sprint 0 - Baseline e Segurança
- [ ] Congelar baseline de código e criar branch de trabalho dedicada (`feature/playground-bi-hardening`) -> Verify: `git branch --show-current`.
- [ ] Executar diagnóstico de mudanças pendentes e gerar relatório de risco -> Verify: script `scripts/sprint0_quality_gate.ps1 -Mode report`.
- [ ] Definir critérios mínimos de release (build, testes smoke, segurança) -> Verify: `scripts/sprint0_quality_gate.ps1 -Mode gate`.
- [ ] Registrar ADRs de decisão (fallback local, roteamento híbrido, políticas de risco) -> Verify: arquivos em `docs/adr/`.

## Sprint 1 - Núcleo Híbrido Sem Dependência Remota
- [ ] Implementar roteador `rules-first` no backend do Playground -> Verify: testes unitários de roteamento.
- [ ] Consolidar fallback local para intents críticas de BI (parquet, filtros, agregações) -> Verify: resposta útil sem `GEMINI_API_KEY`.
- [ ] Adicionar contratos de resposta (`source`, `confidence`, `mode`) -> Verify: schema validado.

## Sprint 2 - Catálogo de Intents BI
- [ ] Criar catálogo de intents e templates por domínio (vendas, ruptura, transferência, ADMAT/UNE) -> Verify: cobertura dos cenários prioritários.
- [ ] Implementar validadores de entrada/saída para SQL/Python gerado -> Verify: testes de segurança e sanitização.
- [ ] Criar suíte de regressão de prompts BI -> Verify: execução automática no CI.

## Sprint 3 - Observabilidade e Governança
- [ ] Instrumentar métricas de latência, fallback rate e erro por tipo -> Verify: endpoint/coleção de métricas.
- [ ] Implementar auditoria por requisição (`request_id`, usuário, origem da resposta) -> Verify: logs estruturados.
- [ ] Aplicar guardrails: RBAC, rate-limit por perfil e circuit breaker -> Verify: testes de integração.

## Sprint 4 - Qualidade e Operação
- [ ] Endurecer pipeline CI com quality gate bloqueante para release -> Verify: PR falha em regressão.
- [ ] Implementar rollout canário e procedimento de rollback -> Verify: runbook documentado/testado.
- [ ] Treinar usuários BI com playbook operacional -> Verify: checklist de operação aprovado.

## Done When
- [ ] Playground responde casos críticos de BI sem depender de LLM remota.
- [ ] LLM remota melhora qualidade quando disponível, sem quebrar operação quando indisponível.
- [ ] Todo release possui rastreabilidade, testes e rollback.
