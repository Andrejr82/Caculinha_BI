# Revisão Robusta do Stack de Chat 2026

## Objetivo

Checklist operacional desta evolução:

- [docs/CHAT_IMPLEMENTATION_CHECKLIST.md](c:/Projetos_BI/Caculinha_BI/docs/CHAT_IMPLEMENTATION_CHECKLIST.md)

Este documento redefine a evolução do chat para um cenário corporativo multiusuário, com uso intensivo por:

- stakeholders
- compradores
- time de business intelligence
- trade
- marketing
- vendas externas

O foco não é “ter um chat bonito”. O foco é ter uma interface resiliente, previsível, auditável e rápida para perguntas de negócio o dia inteiro, sem deixar o usuário preso a bugs de stream, payload quebrado, perda de sessão ou regressão de renderização.

## Diagnóstico Atual do `Chat.tsx`

Arquivo analisado:

- [frontend-solid/src/pages/Chat.tsx](c:/Projetos_BI/Caculinha_BI/frontend-solid/src/pages/Chat.tsx)

Achados concretos:

- o arquivo está grande demais: `2367` linhas
- concentra responsabilidades demais em uma única página
- mistura no mesmo lugar:
  - transporte SSE
  - sanitização de markdown/html
  - normalização de payload
  - estado de sessão
  - histórico
  - anexos
  - voz
  - basket builder
  - renderização de gráfico, tabela, dashboard, imagem, áudio
- usa `EventSource` manual, o que reduz controle sobre:
  - retry
  - headers
  - cancelamento
  - reconexão previsível
- ainda usa sanitização manual com `DOMParser`, o que é melhor que nada, mas não é o melhor padrão de endurecimento para produção corporativa
- o histórico longo não está virtualizado
- o estado do chat ainda depende muito de `createSignal` local, o que dificulta:
  - cache
  - reidratação
  - refetch
  - reconciliação entre sessões
  - estados de erro e retry

## Conclusão de Arquitetura

Para uso corporativo intenso, o chat precisa sair de “página monolítica com várias features” para “shell de orquestração com módulos especializados”.

Arquitetura alvo do frontend:

- `ChatPage`
  - coordena layout, permissões e navegação
- `chat session store`
  - conversa ativa
  - lista de sessões
  - retry/refetch
- `chat stream client`
  - conexão
  - retry
  - cancelamento
  - parser de eventos
- `message normalizer`
  - valida payload
  - converte tipos
  - reduz diferença entre backend e UI
- `message renderers`
  - texto
  - gráfico
  - tabela
  - dashboard
  - automação
  - mídia
- `attachment module`
  - fila
  - status
  - erro
  - progress
- `telemetry layer`
  - erros
  - latência
  - abandono
  - retries

## Melhorias Recomendadas

## 1. Melhorias Aditivas Seguras

Estas podem ser adicionadas sem mexer em major versions do bundler.

### `DOMPurify`

Uso:

- sanitizar o HTML gerado por markdown
- proteger melhor contra XSS e atributos perigosos

Motivo:

- `marked` não deve ser tratado como sanitizador
- o chat renderiza texto livre vindo do backend/LLM

Fonte:

- DOMPurify npm: https://www.npmjs.com/package/dompurify

Recomendação:

- substituir a sanitização manual do `Chat.tsx` por um wrapper centralizado em `chatMarkdown.ts`

### `Zod`

Uso:

- validar `chart_data`
- validar `table_data`
- validar `dashboard_spec`
- validar eventos SSE
- validar assets de imagem/áudio/automação

Motivo:

- o chat recebe payload heterogêneo
- schema validation no frontend reduz bugs silenciosos

Fonte:

- Zod docs: https://zod.dev/

Recomendação:

- criar schemas para:
  - `ChatMessageSchema`
  - `StreamEventSchema`
  - `ChartPayloadSchema`
  - `TablePayloadSchema`
  - `DashboardPayloadSchema`

### `MSW`

Uso:

- mockar backend no frontend
- tornar testes previsíveis para:
  - stream
  - erros de rede
  - payload incompleto
  - retry

Fonte:

- MSW docs: https://mswjs.io/

Recomendação:

- usar em `vitest` para:
  - resposta com gráfico válido
  - resposta com tabela válida
  - stream parcial
  - stream com erro
  - reconexão

### `@microsoft/fetch-event-source`

Uso:

- substituir `EventSource` manual
- melhorar:
  - headers
  - abort
  - retries
  - tratamento de resposta
  - controle de conexão

Fonte:

- Fetch Event Source: https://github.com/Azure/fetch-event-source

Recomendação:

- mover o stream para um cliente dedicado:
  - `frontend-solid/src/lib/chatStreamClient.ts`

### Status Atual da Implementação

O que já foi aplicado no projeto nesta rodada:

- `DOMPurify` instalado e integrado via:
  - `frontend-solid/src/lib/chatMarkdown.ts`
- `Zod` instalado e integrado via:
  - `frontend-solid/src/lib/chatSchemas.ts`
  - `frontend-solid/src/lib/chatPayload.ts`
- stream desacoplado do `Chat.tsx` via:
  - `frontend-solid/src/lib/chatStreamClient.ts`
- `Chat.tsx` atualizado para:
  - usar `renderChatMarkdown`
  - consumir `chatStreamClient`
  - parar de manter sanitização inline
  - parar de depender de `EventSource` direto
- testes adicionados para os novos módulos:
  - `frontend-solid/src/lib/__tests__/chatSchemas.test.ts`
  - `frontend-solid/src/lib/__tests__/chatMarkdown.test.ts`
  - `frontend-solid/src/lib/__tests__/chatStreamClient.test.ts`

Validação já executada:

- `frontend-solid\\node_modules\\.bin\\tsc.cmd --noEmit -p frontend-solid/tsconfig.json`
- `frontend-solid\\node_modules\\.bin\\vitest.cmd --root frontend-solid run`
- smoke E2E:
  - `pages.spec.ts` com `Chat carrega`
  - `chat-context.spec.ts` com gráfico + follow-up

Conclusão desta fase:

- a Fase 1 deixou de ser apenas recomendação e passou a ser realidade no código
- a Fase 2 também avançou no que mais impacta estabilidade operacional do chat:
  - runtime de sessão/capabilities extraído para `frontend-solid/src/hooks/useChatRuntime.ts`
  - fetchers compartilhados em `frontend-solid/src/lib/chatRuntime.ts`
  - `Chat.tsx` deixou de concentrar parte do fetch manual de histórico/capabilities
  - testes do componente `Chat` foram adaptados para rodar com `QueryClientProvider`
- o próximo ganho robusto, sem mexer em upgrade pesado, é continuar tirando responsabilidade da página:
  - histórico detalhado por sessão
  - anexos
  - automação
  - voz

## 2. Melhorias Estruturais Fortes

Estas são as mudanças que realmente deixam o chat robusto para operação de negócio.

### Separar `Chat.tsx` em módulos

Meta:

- `Chat.tsx` virar um shell fino

Extrair:

- `chat-stream-client.ts`
- `chat-message-normalizer.ts`
- `chat-session-store.ts`
- `chat-attachments-store.ts`
- `chat-capabilities-store.ts`
- `chat-markdown.ts`
- `chat-renderers/`

Benefício:

- menor risco de regressão
- testes mais baratos
- manutenção por responsabilidade

### Migrar histórico/sessões para `@tanstack/solid-query`

Uso:

- listar sessões
- carregar histórico
- refresh seguro
- cache de leitura
- invalidação previsível

Fonte:

- TanStack Query docs: https://tanstack.com/query/latest/docs/framework/solid/overview

Recomendação:

- usar `solid-query` para:
  - `conversationHistory`
  - `session list`
  - `capabilities`
  - `attachments metadata`

### Virtualização do histórico

Se o chat for usado o dia inteiro por vários perfis, o histórico vai crescer.

Uso:

- renderizar muitas mensagens sem travar a UI

Fonte:

- TanStack Virtual docs: https://tanstack.com/virtual/v3/docs/introduction

Recomendação:

- virtualizar a lista de mensagens
- manter renderização completa só da janela visível

### Telemetria e replay do frontend

Uso:

- descobrir:
  - em qual mensagem travou
  - qual payload chegou
  - qual interação antecedeu erro
  - onde o usuário abandonou a sessão

Fonte:

- Sentry Session Replay: https://docs.sentry.dev/product/explore/session-replay/web/getting-started/

Recomendação:

- capturar:
  - erro de renderização
  - timeout de stream
  - falha de parse
  - cancelamento
  - tempo de primeira resposta
  - tempo até payload visual

## 3. Melhorias de UX Operacional

### Estados explícitos por capability

O chat precisa distinguir com clareza:

- pensando
- buscando dados
- montando gráfico
- montando tabela
- gerando dashboard
- aguardando anexo
- erro recuperável
- sem dados

Hoje parte disso já existe, mas ainda de forma dispersa.

Recomendação:

- padronizar `message.state`
- padronizar `message.ui_type`
- padronizar `message.recovery_action`

### Retry e recovery explícitos

Cada mensagem crítica precisa suportar:

- reenviar pergunta
- reabrir stream
- tentar payload alternativo
- mostrar diagnóstico amigável

Isso é essencial para:

- compradores
- BI
- marketing
- trade

porque esses perfis não querem “erro técnico”; querem “como seguir”.

### Política de fallback visual

Quando o gráfico falhar:

- exibir tabela

Quando o dashboard falhar:

- exibir cards + tabela

Quando o stream falhar:

- permitir retry no mesmo `request_id` ou recriação automática controlada

## 4. Melhorias de Segurança

### Sanitização centralizada

Hoje há sanitização manual no `Chat.tsx`.

Recomendação:

- mover isso para um módulo único
- adotar `DOMPurify`
- bloquear inline styles, `srcdoc`, handlers e protocolos perigosos

### Validação de payload antes de renderizar

Com `Zod`, qualquer payload inválido:

- não quebra a tela
- cai em fallback
- gera telemetria

### Controle de links e downloads

Todo link renderizado precisa:

- passar por sanitização
- marcar origem
- abrir com `noopener noreferrer`

## 5. Melhorias de Acessibilidade

Para uso corporativo real, isso importa.

Recomendação:

- `aria-live` para novas respostas
- foco previsível após envio
- atalho de teclado para:
  - nova conversa
  - reenviar
  - cancelar stream
- leitura acessível de estados:
  - carregando gráfico
  - erro
  - resposta concluída

Referência útil:

- WAI-ARIA / live regions guidance via MDN e padrões web acessíveis

## 6. Melhorias de Performance

### O que não atualizar agora

Não atualizar agora:

- `vite`
- `vitest`
- `marked`

Motivo:

- grande salto de major version
- alto risco de quebrar build e testes

### O que pode ser feito sem mexer em major

- modularizar o `Chat.tsx`
- adicionar `DOMPurify`
- adicionar `Zod`
- adicionar `MSW`
- trocar `EventSource` por `fetch-event-source`
- virtualizar mensagens
- centralizar normalização de payload

## 7. Prioridade Recomendada

### Fase 1

- `DOMPurify`
- `Zod`
- `chatStreamClient`
- schemas dos eventos

### Fase 2

- modularização do `Chat.tsx`
- `solid-query` para sessões/histórico
- retry explícito

### Fase 3

- virtualização
- telemetria/replay
- métricas de UX

### Fase 4

- upgrades estruturais de versão em canário

## 8. Critérios de Aceite

Só considerar o chat “pronto para escala corporativa” quando:

- `typecheck` estiver verde
- `vitest` estiver verde
- `playwright` estiver verde
- testes cobrirem:
  - texto
  - gráfico
  - tabela
  - dashboard
  - stream interrompido
  - retry
  - anexos
  - histórico
  - permissões/capabilities
- histórico longo não degradar a interface
- payload inválido não quebrar a tela
- erros gerarem observabilidade útil

## 9. Decisão Final

O caminho correto para o chat da Caçula não é “só atualizar dependências”.

O caminho correto é:

- endurecer o contrato de payload
- modularizar o frontend
- melhorar o transporte de stream
- ganhar observabilidade
- só depois discutir upgrades maiores

Em outras palavras:

- primeiro robustez
- depois escalabilidade
- só então atualização agressiva de stack
