# ADR-005: Dashboard Chat-First

## Status
Accepted

## Contexto
Usuários de negócio solicitam análises em linguagem natural e esperam dashboard interativo como saída primária, sem depender de construção manual fora do chat.

## Decisão
Adotar abordagem chat-first para dashboards:
- rota explícita de intenção para pedidos de dashboard;
- contrato canônico `dashboard_spec` no backend;
- renderização nativa no frontend de chat com fallback para gráfico único quando necessário.

## Consequências
- Positivas: redução de tempo para insight e melhor experiência de autoatendimento.
- Negativas: aumento da superfície de validação entre backend/frontend.
- Mitigação: testes de contrato SSE + testes de renderização por cenário de segmento/período.
