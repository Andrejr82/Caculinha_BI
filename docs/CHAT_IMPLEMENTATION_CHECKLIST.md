# Checklist de Implementação do Chat

## Objetivo

Acompanhar, com checkboxes, as entregas necessárias para o chat ficar robusto para uso intensivo por:

- stakeholders
- compras
- business intelligence
- trade
- marketing
- vendas externas

Este checklist separa:

- o que já foi implementado
- o que ainda está pendente
- o que é opcional para depois da apresentação

## 1. Guardrails e Contrato de Resposta

- [x] Corrigir regressão de gráfico que inferia segmento inválido como `DA`
- [x] Endurecer guardrail semântico para gráfico
- [x] Endurecer guardrail semântico para tabela
- [x] Endurecer guardrail semântico para dashboard
- [x] Endurecer guardrail semântico para export
- [x] Barrar resposta de basket fora de contexto
- [x] Tratar respostas honestas de `no_data` sem cair em falso bloqueio
- [x] Garantir que o evento `final` carregue payload estruturado quando houver gráfico/tabela/dashboard
- [x] Garantir que anexos não contaminem a query efetiva

## 2. Endurecimento do Frontend do Chat

### 2.1 Sanitização e renderização

- [x] Remover sanitização inline do `Chat.tsx`
- [x] Centralizar renderização de markdown em `chatMarkdown.ts`
- [x] Integrar `DOMPurify`
- [x] Manter sanitização de links com `noopener noreferrer`
- [x] Bloquear links perigosos como `javascript:`

### 2.2 Validação de payload

- [x] Criar schemas com `Zod` para eventos do stream
- [x] Criar schemas com `Zod` para `chart_spec`
- [x] Criar schemas com `Zod` para `table_data`
- [x] Criar schemas com `Zod` para `dashboard_spec`
- [x] Criar schemas com `Zod` para assets de imagem e áudio
- [x] Criar schemas com `Zod` para estado de automação
- [x] Integrar validação por schema em `chatPayload.ts`

### 2.3 Transporte de stream

- [x] Substituir uso direto de `EventSource` por cliente dedicado
- [x] Criar `chatStreamClient.ts`
- [x] Integrar `@microsoft/fetch-event-source`
- [x] Suportar `abort/close` via conexão controlada
- [x] Tratar erro de payload inválido no stream
- [x] Tratar erro de transporte no stream

### 2.4 Sessão e histórico

- [x] Extrair fetchers de runtime do chat para módulo dedicado
- [x] Criar `chatRuntime.ts`
- [x] Criar `useChatRuntime.ts`
- [x] Mover capabilities para runtime compartilhado
- [x] Mover lista de sessões para runtime compartilhado
- [x] Integrar `solid-query` ao runtime do chat
- [x] Adaptar testes do `Chat` para `QueryClientProvider`

## 3. Estrutura do `Chat.tsx`

- [x] Reduzir responsabilidade do `Chat.tsx` no fluxo de stream
- [x] Reduzir responsabilidade do `Chat.tsx` na sanitização de markdown/html
- [x] Reduzir responsabilidade do `Chat.tsx` em capabilities e lista de sessões
- [ ] Extrair histórico detalhado por sessão para módulo próprio
- [ ] Extrair fluxo de anexos para módulo próprio
- [ ] Extrair fluxo de voz para módulo próprio
- [ ] Extrair fluxo de automação para módulo próprio
- [ ] Extrair renderers por tipo de mensagem
- [ ] Transformar `Chat.tsx` em shell fino de orquestração

## 4. Testes do Frontend

- [x] Adicionar testes de schema do chat
- [x] Adicionar testes de markdown sanitizado
- [x] Adicionar testes do stream client
- [x] Manter testes do `Chat` passando
- [x] Manter typecheck do frontend verde
- [x] Validar `Vitest` do frontend verde

## 5. Testes E2E e Smoke

- [x] Validar `Chat carrega` com Playwright
- [x] Validar fluxo real `gráfico -> follow-up comercial`
- [x] Validar backend do chat com `pytest`
- [x] Validar integração de documento/routing do chat com `pytest`
- [x] Validar fluxo de anexos em browser real
- [x] Validar fluxo de tabela em browser real
- [x] Validar fluxo de dashboard em browser real
- [x] Validar fluxo de exportação em browser real

## 6. Robustez Operacional para Multiusuário

- [x] Preparar o chat para usar backend transacional no estado da conversa
- [x] Reduzir dependência de estado local frágil no frontend
- [x] Melhorar previsibilidade do histórico e da sessão ativa
- [ ] Virtualizar histórico longo de mensagens
- [ ] Adicionar telemetria mais rica de abandono/retry
- [ ] Adicionar replay/sessão do frontend
- [ ] Adicionar fallback visual automático `dashboard -> tabela`
- [ ] Adicionar fallback visual automático `gráfico -> tabela`

## 7. Segurança do Chat

- [x] Centralizar sanitização do markdown
- [x] Validar payload antes de renderizar
- [x] Bloquear links inseguros
- [ ] Migrar tokens do frontend para cookie `HttpOnly`
- [ ] Integrar monitoramento de erros do frontend com Sentry
- [ ] Endurecer política de CSP no frontend

## 8. Documentação e Governança

- [x] Revisar `CHAT_UPDATE_REVIEW_2026.md`
- [x] Manter documento de robustez do frontend
- [x] Manter documento de stack de testes do chat
- [x] Criar checklist operacional com checkboxes
- [ ] Criar checklist de aprovação final da demo

## 9. Estado Atual para a Apresentação

### Concluído

- [x] Stream mais robusto
- [x] Payload validado por schema
- [x] Markdown sanitizado centralmente
- [x] Query sem contaminação por anexos
- [x] Capabilities e lista de sessões parcialmente desacopladas do `Chat.tsx`
- [x] Testes unitários do frontend verdes
- [x] Typecheck verde
- [x] Smoke E2E do chat verde
- [x] Fluxo de contexto de negócio validado em browser real

### Pendências não bloqueantes para amanhã

- [ ] Modularização total do `Chat.tsx`
- [ ] Virtualização do histórico
- [ ] MSW para cenários determinísticos de stream
- [ ] Sentry/Replays no frontend
- [x] E2E completo de anexos/dashboard/export

## 10. Última Validação Executada

- [x] `frontend-solid\\node_modules\\.bin\\tsc.cmd --noEmit -p frontend-solid/tsconfig.json`
- [x] `frontend-solid\\node_modules\\.bin\\vitest.cmd --root frontend-solid run`
- [x] `python -m pytest backend/tests/integration/test_chat_endpoint.py backend/tests/test_chat_service_document_rag.py -q`
- [x] `frontend-solid\\node_modules\\.bin\\playwright.cmd test frontend-solid/tests/integration/pages.spec.ts -g "Chat carrega" --config frontend-solid/playwright.config.ts`
- [x] `frontend-solid\\node_modules\\.bin\\playwright.cmd test frontend-solid/tests/integration/chat-context.spec.ts -g "keeps context from chart request into 7-day commercial plan follow-up" --config frontend-solid/playwright.config.ts`
- [x] `python -m pytest backend/tests/test_chatbi_deterministic_rules.py backend/tests/test_chat_service_document_rag.py backend/tests/test_universal_tool_selection.py -q`
- [x] `frontend-solid\\node_modules\\.bin\\playwright.cmd test frontend-solid/tests/integration/chat-functionalities.spec.ts --config frontend-solid/playwright.config.ts`
