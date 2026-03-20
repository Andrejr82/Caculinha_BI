# Plano de Implementação - Playground BI + ChatBI (Capacidade de Agente)

## Objetivo
Transformar o Playground/ChatBI em um agente de BI confiável para operação diária, com capacidade explícita de gerar dashboard interativo por segmento, pesquisa de mercado com evidência, cálculos complexos e execução resiliente (determinística + LLM com fallback).

## Metas de capacidade (equivalência prática)
- [x] BI interno (consulta, agregação, gráfico, dashboard): >= 95% de sucesso nos casos críticos -> Verify: suíte de avaliação por domínio.
- [x] Pesquisa de mercado com fontes públicas: >= 85% de respostas com evidência citável -> Verify: validação automática de links/fontes.
- [x] Cálculo complexo (EOQ, previsão, sensibilidade): >= 95% de concordância com baseline de referência -> Verify: regressão numérica.
- [x] Confiabilidade operacional: erro 5xx < 1% e P95 <= 15s em consultas complexas -> Verify: painel de SLO.

## Escopo
- Inclui: dashboard interativo por segmento no ChatBI, robustez de stream, RBAC orientado a capacidade, orquestração multi-modelo por tarefa, evals bloqueantes e observabilidade.
- Não inclui nesta fase: multimodalidade avançada (voz/imagem), computer-use e automação de desktop.

## Sprint 0 - Baseline, Segurança e Governança
- [x] Congelar baseline de código e criar branch de trabalho dedicada (`feature/playground-bi-hardening`) -> Verify: `git branch --show-current`.
- [x] Executar diagnóstico de mudanças pendentes e gerar relatório de risco -> Verify: `scripts/sprint0_quality_gate.ps1 -Mode report`.
- [x] Definir critérios mínimos de release (build, smoke, segurança, evals) -> Verify: `scripts/sprint0_quality_gate.ps1 -Mode gate`.
- [x] Registrar ADRs de decisão (fallback local, roteamento híbrido, RBAC de capacidade, dashboard chat-first) -> Verify: arquivos em `docs/adr/`.

## Sprint 1 - Confiabilidade de Chat e UX de Erro
- [x] Corrigir falhas silenciosas do stream no frontend (`stream-token`/SSE) com erro visível ao usuário -> Verify: teste de integração SSE e teste manual com backend indisponível.
- [x] Garantir limpeza de estado de stream (`EventSource`) em erro/cancelamento -> Verify: sem spinner infinito e sem mensagem otimista vazia.
- [x] Normalizar contrato de eventos SSE (`tool_progress`, `text`, `chart`, `table`, `final`, `error`) -> Verify: testes de contrato no backend + frontend.

## Sprint 2 - Capacidade de Dashboard Interativo no ChatBI
- [x] Reintroduzir/garantir tool de dashboard no conjunto principal do agente (`gerar_dashboard_executivo`) -> Verify: tool disponível no escopo `analyst` e `business_user`.
- [x] Adicionar rota de intenção explícita para pedido de dashboard por segmento/UNE/período -> Verify: testes de roteamento para queries "dashboard".
- [x] Definir contrato de resposta de dashboard (`dashboard_spec`, filtros aplicados, período, fonte) -> Verify: schema validado e renderização no frontend.
- [x] Implementar renderização de dashboard no chat (múltiplos widgets + filtros básicos) -> Verify: caso E2E "dashboard interativo do segmento ARTES".
- [x] Criar fallback para gráfico único quando dashboard não for possível -> Verify: resposta útil e justificada.

## Sprint 3 - Dados Internos + Pesquisa de Mercado com Evidência
- [x] Consolidar fallback local para intents críticas de BI (parquet, filtros, agregações) -> Verify: resposta útil sem `GEMINI_API_KEY`.
- [x] Melhorar pesquisa de mercado com priorização de fontes, citação e score de confiança -> Verify: resposta contém fontes, domínio e qualidade mínima.
- [x] Corrigir erros conhecidos de pesquisa (timeout excessivo e cálculo interno de preço) -> Verify: regressão dos casos de mercado sem erro SQL.
- [x] Adicionar contratos de resposta (`source`, `confidence`, `mode`, `citations`) -> Verify: schema validado.

## Sprint 4 - Cálculo Complexo e Orquestração Multi-Modelo
- [x] Integrar sandbox de cálculo como caminho de primeira classe para consultas matemáticas complexas -> Verify: casos de simulação/sensibilidade aprovados.
- [x] Configurar roteamento por tarefa para provedores LLM (não apenas fallback global) -> Verify: teste de failover por tipo de tarefa.
- [x] Implementar auto-recuperação de tool failure (retry seguro + fallback semântico) -> Verify: testes de erro forçado de tool.
- Implementação técnica (Sprint 4):
  - `backend/app/core/agents/caculinha_bi_agent.py`: rota `calculation_sandbox` com resposta determinística (`source/mode/confidence/citations`), fallback semântico de tools e propagação de `task_type` para o LLM.
  - `backend/app/core/llm_factory.py`: `SmartLLM` com cadeia de provedores por tarefa (`task_type`) mantendo fallback global.
  - `backend/app/config/settings.py`: nova configuração `LLM_TASK_PROVIDER_ROUTING` para definir ordem por domínio de tarefa.
  - Testes adicionados: `backend/tests/test_smart_llm_task_routing.py` e expansão de `backend/tests/test_chatbi_deterministic_rules.py`.

## Sprint 5 - Observabilidade, Evals e Operação
- [x] Instrumentar métricas de qualidade semântica (`tool_selection_accuracy`, `no_data_false_positive`, `citation_coverage`) -> Verify: endpoint/coleção de métricas.
- [x] Implementar auditoria por requisição (`request_id`, usuário, origem da resposta, tools executadas) -> Verify: logs estruturados ponta a ponta.
- [x] Criar suíte de avaliação bloqueante por domínio (dados internos, dashboard, mercado, cálculo) -> Verify: CI falha abaixo das metas.
- [x] Aplicar guardrails: RBAC, rate-limit por perfil e circuit breaker -> Verify: testes de integração e carga.
- Implementação técnica (Sprint 5):
  - `backend/app/services/chat_service_v3.py`: `request_id` ponta a ponta, auditoria estruturada por requisição, rate-limit por perfil/usuário, métricas semânticas e propagação de `tool_calls`.
  - `backend/app/api/v1/endpoints/chat.py`: geração e propagação de `request_id` no SSE, incluindo evento `final` e payloads de erro/dashboard/chart/table.
  - `backend/app/core/llm_factory.py`: circuit breaker por provedor (`llm_provider_*`) nas chamadas síncronas (`get_completion` e `generate_with_history`) com fallback automático quando circuito estiver aberto.
  - `backend/app/api/v1/endpoints/admin_dashboard.py`: novos KPIs de qualidade semântica no `/admin/dashboard/chat-slo`.
  - `backend/tests/llmops/test_domain_eval_gate.py` e `.github/workflows/ci.yml`: gate explícito por domínio no CI.

## Sprint 6 - Go-Live Controlado
- [x] Endurecer pipeline CI com quality gate bloqueante para release -> Verify: PR bloqueado em regressão.
- [x] Implementar rollout canário e procedimento de rollback -> Verify: runbook documentado e simulado.
- [x] Treinar usuários BI com playbook operacional focado em dashboards/chat -> Verify: checklist de operação aprovado.
- Implementação técnica (Sprint 6):
  - `.github/workflows/ci.yml`: execução obrigatória de `scripts/sprint0_quality_gate.ps1 -Mode gate` como bloqueio de release.
  - `scripts/chatbi_canary_rollback_drill.ps1`: drill executável para validação de canário/rollback com evidências mínimas.
  - `backend/tests/test_chat_canary_gate.py`: testes automatizados de escopo de acesso `CHAT_CANARY_*`.
  - `docs/CHATBI_SPRINT6_GO_LIVE_RUNBOOK.md`: runbook consolidado de go-live, expansão e rollback.
  - `docs/CHATBI_PLAYBOOK_TREINAMENTO_DASHBOARD.md`: playbook operacional de treinamento para usuários de negócio.

## Done When
- [x] ChatBI gera dashboard interativo por segmento com filtros e evidência, de forma consistente.
- [x] Agente responde casos críticos de BI mesmo sem LLM remota (fallback determinístico útil).
- [x] LLM melhora qualidade quando disponível, sem quebrar operação quando indisponível.
- [x] Releases têm rastreabilidade, evals bloqueantes e rollback testado.
