# Chat Frontend Robustness

## Objetivo
Elevar a robustez do chat do `frontend-solid` para que:

- perguntas textuais, tabulares, gráficas, dashboard, mídia e automação convivam no mesmo fluxo;
- anexos não contaminem a intenção principal da pergunta;
- payloads do backend não se percam no streaming;
- o frontend continue exibindo a resposta correta mesmo quando parte do stream falhar ou chegar fora de ordem.

## Diagnóstico do `Chat.tsx`
Arquivo principal analisado:

- `frontend-solid/src/pages/Chat.tsx`

### Pontos fortes atuais
- já há suporte a:
  - SSE/streaming;
  - gráfico;
  - tabela;
  - dashboard;
  - imagem;
  - áudio;
  - citações;
  - automação assistida;
  - anexos;
  - histórico por sessão.
- o arquivo já sanitiza links e HTML antes do `innerHTML`;
- há integração com `PlotlyChart`, `DataTable`, `ChatDashboardRenderer` e `ChatAutomationCard`.

### Fragilidades reais encontradas
1. `Chat.tsx` concentra transporte, parsing, sessão, telemetria, anexos, voz, builder de basket e renderização no mesmo arquivo.
2. A query efetiva ainda estava sendo contaminada por nomes de anexos, apesar do backend já ter guardrails para isso.
3. O frontend dependia demais dos eventos intermediários do SSE.
   - Se gráfico/tabela/dashboard não chegassem antes do `final`, o payload podia se perder.
4. O stream aceita formatos próximos, mas ainda pouco normalizados.
   - `chart_spec` x `chart_data`
   - `data` x `table_data`
5. O frontend usa `marked` com sanitização manual.
   - funciona, mas é um ponto sensível de segurança e manutenção.

## Correções imediatas aplicadas
### 1. Query efetiva sem contaminação de anexos
O frontend deixou de inserir automaticamente:

- `Considere os anexos desta sessão: ...`

na query efetiva enviada ao backend.

Isso preserva o papel correto dos anexos:

- contexto auxiliar;
- nunca fonte principal implícita.

### 2. Materialização de payload no evento final
O fluxo SSE ficou mais resiliente:

- backend agora replica no `final`:
  - `chart_data/chart_spec`
  - `table_data`
  - `dashboard_spec`
- frontend agora consome esses payloads também no `final`

Isso reduz perda de renderização quando o usuário recebe:

- texto final sem ter capturado todos os eventos intermediários;
- stream parcial;
- falha de ordem entre eventos.

### 3. Normalização mais tolerante no frontend
O `Chat.tsx` agora aceita de forma robusta:

- `chart_spec` ou `chart_data`
- `data` ou `table_data`

## Pesquisa de ferramentas recomendadas
As recomendações abaixo foram selecionadas por aderência ao stack atual e ao tipo de problema do projeto.

### 1. DOMPurify
Uso recomendado:

- substituir a sanitização manual de HTML/Markdown por uma sanitização battle-tested.

Benefício:

- reduz risco de XSS em respostas com markdown e links;
- integra melhor com políticas modernas como Trusted Types.

Referência:

- DOMPurify no npm: <https://www.npmjs.com/package/dompurify>

### 2. TanStack Query
O projeto já usa:

- `@tanstack/solid-query`

Uso recomendado no chat:

- mover capacidades, histórico, upload status e refresh de sessão para query/mutation controladas;
- usar retry, stale state, invalidação e cancelamento de forma centralizada.

Benefício:

- menos estado manual espalhado;
- menos regressão por race condition;
- melhor previsibilidade para sessão/histórico/capabilities.

Referência:

- TanStack Query docs: <https://tanstack.com/query/latest>

### 3. TanStack Virtual
Uso recomendado:

- virtualizar listas longas de mensagens e histórico de conversas.

Benefício:

- melhora performance quando a conversa cresce;
- reduz re-render desnecessário;
- evita degradação do DOM em sessões extensas.

Referência:

- TanStack Virtual docs: <https://tanstack.com/virtual/latest>

### 4. `fetch-event-source`
Uso recomendado:

- substituir `EventSource` puro por um cliente SSE com:
  - headers;
  - retry controlado;
  - abort;
  - reconexão governada;
  - melhor observabilidade.

Benefício:

- menos acoplamento ao token efêmero na URL;
- melhor controle de falha de transporte;
- melhor tratamento de timeouts e reconexão.

Referência:

- Fetch Event Source: <https://github.com/Azure/fetch-event-source>

### 5. Zod
Uso recomendado:

- validar payloads do SSE e payloads finais antes de atualizar `messages`.

Benefício:

- impede que payload parcial ou inválido contamine a UI;
- facilita evolução de contratos do backend.

Referência:

- Zod docs: <https://zod.dev/>

### 6. Sentry Browser + Replay/Tracing
Uso recomendado:

- monitorar erros do chat em produção;
- capturar regressões de stream, payload e renderização.

Benefício:

- visibilidade real do que quebra no navegador do usuário;
- correlação entre erro de frontend, sessão e backend.

Referência:

- Sentry JavaScript docs: <https://docs.sentry.io/platforms/javascript/>

## Recomendações por prioridade
### Prioridade 1
- extrair o parser de eventos SSE para um módulo próprio;
- validar payloads com Zod;
- trocar sanitização manual por DOMPurify;
- parar de enriquecer query com metadados de anexo no frontend.

### Prioridade 2
- mover histórico/capabilities/uploads para `solid-query`;
- replicar payload importante no `final` do stream;
- centralizar normalização de mensagens do backend.

### Prioridade 3
- virtualizar lista de mensagens;
- instrumentar Sentry e telemetria estruturada;
- avaliar migração de `EventSource` para `fetch-event-source`.

## Arquitetura recomendada para o chat
Separar o `Chat.tsx` em módulos:

1. `chat-message-normalizer`
   - transforma resposta backend/SSE em `Message`.

2. `chat-stream-client`
   - controla conexão, retry, abort e parsing de eventos.

3. `chat-session-store`
   - estado de sessão, histórico, capabilities e anexos.

4. `chat-renderers`
   - texto/markdown;
   - tabela;
   - gráfico;
   - dashboard;
   - mídia;
   - automação.

5. `chat-validators`
   - schemas de payload;
   - guardrails de compatibilidade frontend/backend.

## O que muda para o usuário final
Com esse endurecimento:

- o chat deixa de depender tanto da ordem perfeita do stream;
- anexos param de influenciar indevidamente consultas da base local;
- respostas de gráfico/tabela/dashboard ficam mais estáveis;
- a UI fica mais preparada para qualquer tool do LLM que devolva payload estruturado.

## Estado após esta rodada
Já corrigido:

- query efetiva sem metadados automáticos de anexo;
- `final` do stream com payload visual/tabular;
- frontend aceitando payload final para gráfico/tabela/dashboard.

Ainda recomendado:

- modularização do `Chat.tsx`;
- validação de payload com schema;
- sanitização com biblioteca dedicada;
- transporte SSE mais robusto que `EventSource` puro.
