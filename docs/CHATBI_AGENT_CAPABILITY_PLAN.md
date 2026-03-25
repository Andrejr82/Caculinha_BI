# ChatBI Agent Capability Plan (Detalhado)

## 1. Objetivo
Evoluir o ChatBI para capacidade de agente de BI de alto desempenho, com foco em:
- Dashboard interativo por segmento dentro do chat.
- Consultas de dados internos com alta confiabilidade.
- Pesquisa de mercado com evidência citável.
- Cálculos complexos com sandbox seguro.
- Operação resiliente com fallback e quality gates.

## 2. Escopo e Princípios

### Incluído nesta fase
- Dashboard interativo chat-first.
- Robustez de stream (SSE) no frontend.
- RBAC orientado a capacidade de negócio.
- Orquestração multi-modelo por tarefa.
- Observabilidade semântica e regressão bloqueante.

### Fora de escopo nesta fase
- Multimodalidade avançada (voz/imagem).
- Computer-use automation.
- Automação de desktop/sistema operacional.

### Princípios operacionais
- Fallback determinístico sempre disponível.
- Resposta com evidência e recorte aplicado.
- Segurança por padrão (RLS, RBAC, rate-limit, auditoria).
- Mudança só entra com validação automática.

## 3. Estado Atual (Resumo Técnico)
- Frontend de chat já renderiza texto, tabela e gráfico via SSE.
- Backend já possui agente com roteamento por intenção e execução governada de tools.
- Pesquisa de mercado já existe, mas com variabilidade por fonte/timeout.
- Cálculo complexo existe em componentes separados, ainda com integração desigual no fluxo principal.
- Testes de frontend do chat estão desalinhados com a UI atual.

## 4. Capacidade-Alvo por Domínio

| Domínio | Capacidade alvo | Meta |
|---|---|---|
| Dados internos | Consulta, agregação, gráfico, dashboard | >=95% sucesso |
| Dashboard | Dashboard interativo por segmento/UNE/período | >=95% sucesso |
| Mercado | Pesquisa externa com fontes e confiança | >=85% com citação |
| Cálculo | EOQ, previsão, sensibilidade | >=95% concordância |
| Operação | Latência e erro em produção | 5xx <1%, P95 <= 15s |

## 5. Workstreams Técnicos

## W1. Confiabilidade de Chat (Frontend + SSE)
- Corrigir falhas silenciosas de stream-token/SSE.
- Garantir limpeza de estado `EventSource` em erro/cancelamento.
- Padronizar tratamento de eventos SSE e fallback de UI.

### Arquivos principais
- `frontend-solid/src/pages/Chat.tsx`
- `backend/app/api/v1/endpoints/chat.py`

### Critério de aceite
- Nenhum cenário deixa mensagem otimista vazia sem erro explícito.
- Não há spinner infinito após falha de stream.

## W2. Dashboard Interativo no ChatBI
- Garantir disponibilidade da tool de dashboard no set principal do agente.
- Criar contrato `dashboard_spec` para múltiplos widgets no chat.
- Implementar renderização dedicada de dashboard no frontend.
- Fallback automático para gráfico único quando dashboard completo não for possível.

### Contrato mínimo sugerido
```json
{
  "type": "dashboard",
  "dashboard_spec": {
    "title": "Dashboard Segmento ARTES",
    "filters": {"segmento": "ARTES", "periodo": "30d"},
    "widgets": [
      {"kind": "kpi", "id": "venda_total", "value": 319947.24},
      {"kind": "chart", "id": "venda_por_une", "chart_spec": {}},
      {"kind": "table", "id": "top_produtos", "rows": []}
    ]
  },
  "source": "deterministic_tool",
  "confidence": 0.93
}
```

### Arquivos principais
- `backend/app/core/agents/caculinha_bi_agent.py`
- `backend/app/core/utils/query_router.py`
- `frontend-solid/src/pages/Chat.tsx`
- `frontend-solid/src/components/*` (novo renderer de dashboard)

### Critério de aceite
- Query "dashboard interativo do segmento ARTES" retorna `dashboard_spec` válido.
- Dashboard renderiza no chat com pelo menos 3 widgets (KPI + gráfico + tabela).

## W3. Pesquisa de Mercado com Evidência
- Padronizar saída de pesquisa com `citations`, `sources` e `confidence`.
- Melhorar priorização de fontes e reduzir timeout total improdutivo.
- Corrigir regressões de query SQL interna relacionada ao enriquecimento de preço.

### Arquivos principais
- `backend/app/core/tools/competitive_intelligence_tool.py`
- `backend/app/api/v1/endpoints/chat.py`

### Critério de aceite
- Toda resposta de mercado relevante inclui fontes e score de confiança.
- Cenários críticos sem evidência retornam mensagem de ação clara (sem falso positivo).

## W4. Cálculo Complexo e Sandbox
- Integrar execução de cálculo complexo no caminho principal com política de segurança.
- Padronizar erros de cálculo para resposta acionável de negócio.
- Expandir cenários de sensibilidade/simulação com timeout controlado.

### Arquivos principais
- `backend/app/core/agents/code_gen_agent.py`
- `backend/app/services/chat_service_v3.py`
- `backend/app/core/agents/caculinha_bi_agent.py`

### Critério de aceite
- Suite de cálculos passa com concordância >=95% versus baseline.
- Erros são tratados sem vazar detalhes técnicos.

## W5. RBAC de Capacidade e Governança
- Revisar mapeamento de role para não bloquear capacidades essenciais de negócio.
- Definir perfil funcional (`business_user`) com acesso controlado a dados/mercado/cálculo.
- Manter trilha de auditoria por requisição.

### Arquivos principais
- `backend/app/services/chat_service_v3.py`
- `backend/app/core/utils/tool_scoping.py`
- `backend/app/api/dependencies.py`

### Critério de aceite
- Usuário de negócio autorizado consegue executar os 3 domínios críticos.
- Perfis restritos continuam sem exposição indevida de dados.

## W6. Evals, Observabilidade e Operação
- Criar evals por domínio com gate bloqueante no CI.
- Instrumentar métricas semânticas de qualidade.
- Concluir runbook de canary/rollback com simulação.

### Métricas mínimas
- `tool_selection_accuracy`
- `citation_coverage`
- `no_data_false_positive_rate`
- `dashboard_success_rate`
- `chat_latency_p95`
- `chat_5xx_rate`

### Critério de aceite
- Release bloqueado abaixo das metas.
- Operação com SLO estável por 7 dias.

## 6. Plano de Testes (obrigatório)

## Unitário
- Roteamento de dashboard por intenção.
- Validação de contrato `dashboard_spec`.
- Normalização de erro SSE/frontend.

## Integração
- Chat -> stream-token -> SSE -> render dashboard.
- Mercado com citação em cenários com e sem evidência.
- Cálculo complexo com fallback seguro.

## E2E
- Caso 1: dashboard por segmento.
- Caso 2: pesquisa de mercado com fontes.
- Caso 3: cálculo de EOQ + explicação executiva.

## Não-funcional
- Latência P95 simples e complexa.
- Teste de carga de sessões concorrentes.
- Teste de canário com rollback.

## 7. Riscos e Mitigações
- Risco: variabilidade de provedores LLM.
- Mitigação: roteamento por tarefa + fallback determinístico.

- Risco: regressão de UX no stream.
- Mitigação: contrato SSE estável + testes de integração frontend.

- Risco: bloqueio por RBAC excessivo.
- Mitigação: role de negócio explícita com escopo mínimo funcional.

- Risco: custo operacional subir com tools externas.
- Mitigação: budget por request, timeout total e cache orientado a domínio.

## 8. Entregáveis
- Plano consolidado atualizado no root:
  - `playground-bi-implementation-plan.md`
- Documento técnico detalhado:
  - `docs/CHATBI_AGENT_CAPABILITY_PLAN.md`

## 9. Done When (detalhado)
- ChatBI entrega dashboard interativo por segmento com evidência e filtros.
- Casos críticos de BI funcionam sem dependência exclusiva de LLM remota.
- Pesquisa de mercado e cálculos complexos passam metas de qualidade.
- CI bloqueia regressão e operação possui canário/rollback testados.
