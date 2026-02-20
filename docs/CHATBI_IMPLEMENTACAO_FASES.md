# Plano de Implementação - Checklist ChatBI Enterprise

## Janela sugerida
- Fase 1: 0-30 dias (Risco alto, valor imediato)
- Fase 2: 31-60 dias (Confiabilidade e escala)
- Fase 3: 61-90 dias (Produto enterprise completo)

## Fase 1 (0-30 dias)
1. Governança de acesso real no chat
- Remover role fixa `analyst` no serviço e usar role do usuário autenticado.
- Garantir RLS em todas as ferramentas usadas pelo agente.
- Entrega: testes de permissão por perfil.

2. Segurança de stream
- Manter token efêmero obrigatório no chat stream.
- Remover fallback legado com token em query string para chat.
- Entrega: teste de autenticação SSE e auditoria de logs.

3. Feedback e qualidade contínua
- Coletar feedback funcional (positivo/negativo/parcial) por resposta.
- Integrar feedback ao ciclo de melhoria e dashboards de qualidade.
- Entrega: endpoint + UI + métrica de taxa de utilidade.

### Critério de saída da Fase 1
- Zero bloqueio crítico em segurança/governança.
- Fluxo de feedback operacional para usuários finais.

## Fase 2 (31-60 dias)
1. Observabilidade completa
- Métricas de latência, erro, cache, custo/token e uso de ferramentas.
- Dash operacional com SLO/SLA.

2. Robustez de execução
- Retry/circuit breaker por provedor LLM.
- Fallback determinístico quando tool crítica indisponível.

3. Performance
- Medir e otimizar P95 simples/complexo.
- Warm-up de componentes críticos no startup.

### Critério de saída da Fase 2
- SLO estável por 7 dias.
- Erro 5xx dentro de meta definida.

## Fase 3 (61-90 dias)
1. Relatórios robustos no chat
- Templates oficiais por processo de compras/comercial.
- Saída padronizada (Resumo, Tabela, SQL/Python, Ação).

2. LLMOps
- Dataset versionado de perguntas reais.
- Regressão automatizada por release.

3. Go-live controlado
- Canary por grupo de usuários.
- Runbook e rollback testados.

### Critério de saída da Fase 3
- Operação com aprovação formal de TI + negócio.
- Checklist de go-live 100% validado.

## KPIs de acompanhamento
- Taxa de sucesso das perguntas reais (%).
- P95 simples e complexo (s).
- Taxa de erro factual (%).
- Taxa de feedback útil (%).
- Erro 5xx (%).
