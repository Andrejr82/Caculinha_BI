# Chat Testing Stack

## Objetivo

Deixar o fluxo do chat robusto em quatro camadas:

- testes puros de normalização e contratos
- testes de componente/UI
- testes E2E do fluxo real
- guardrails e telemetria para diagnosticar regressões

## Stack recomendada

### 1. Vitest

Usar para:

- helpers puros de payload e parsing
- contratos do stream
- componentes do chat

Motivo:

- rápido para feedback local
- integra bem com Vite
- cobre regressões de transformação de payload antes de virar bug visual

Status no projeto:

- já em uso
- agora executado com `--root frontend-solid` no monorepo

### 2. Playwright

Usar para:

- login
- carregamento do chat
- geração real de gráfico
- follow-up contextual
- anexos e exportação

Motivo:

- valida a UI completa com frontend + backend
- usa auto-waiting e assertions orientadas ao comportamento real do usuário

Status no projeto:

- já em uso
- `playwright.config.ts` ajustado para subir o frontend com `npm run dev`

### 3. Zod

Usar para:

- validar payload do SSE antes de atualizar a store/UI
- validar contratos de `final`, `chart`, `table`, `dashboard`, `image`, `audio`

Motivo:

- evita aceitar payload parcialmente inválido
- reduz regressão silenciosa no `Chat.tsx`

Status no projeto:

- recomendado para próxima etapa

### 4. Mock Service Worker (MSW)

Usar para:

- mockar `/api/v1/chat/stream-token`
- mockar payloads REST do chat/history/capabilities
- simular erros de rede e respostas degradadas

Motivo:

- desacopla testes de componente do backend real
- permite reproduzir falhas de stream e edge cases de forma determinística

Status no projeto:

- recomendado para próxima etapa

### 5. `@microsoft/fetch-event-source`

Usar para:

- substituir o uso direto de `EventSource`
- permitir retry, abort, headers e maior controle do stream

Motivo:

- o chat depende fortemente de SSE
- melhora observabilidade e controle do canal de streaming

Status no projeto:

- recomendado para próxima etapa

## Ordem recomendada

1. Manter `Vitest + Playwright` como baseline.
2. Adicionar `Zod` para schema do stream.
3. Adicionar `MSW` para testes determinísticos do frontend.
4. Migrar SSE para `fetch-event-source`.

## Resultado esperado

Com essa combinação, o chat fica protegido contra:

- regressão de payload do backend
- perda de gráfico no `final`
- contaminação por anexos
- mismatch entre capability esperada e resposta entregue
- bugs de renderização que só aparecem no navegador real
