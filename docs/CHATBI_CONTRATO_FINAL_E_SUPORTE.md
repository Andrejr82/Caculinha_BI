# ChatBI Contrato Final e Guia de Suporte

## Escopo congelado
Este documento descreve o contrato operacional da stack ativa do chat:
- Frontend: `frontend-solid/src/pages/Chat.tsx`
- API principal: `backend/app/api/v1/endpoints/chat.py`
- Orquestracao: `backend/app/services/chat_service_v3.py`
- Automacoes: `backend/app/services/chat_automation_service.py`

## Endpoints suportados
- `GET /api/v1/chat/capabilities`
- `POST /api/v1/chat/stream-token`
- `GET /api/v1/chat/stream`
- `POST /api/v1/chat`
- `POST /api/v1/chat/feedback`
- `GET /api/v1/chat/history`
- `DELETE /api/v1/chat/history/{session_id}`
- `POST /api/v1/chat/automation/approve`
- `POST /api/v1/chat/automation/reject`
- `GET /api/v1/chat/automation/history`
- `GET /api/v1/chat/automation/artifacts/{approval_id}/{filename}`
- `POST /api/v1/ingest/file`
- `POST /api/v1/ingest/image`

## Eventos SSE obrigatorios
- `tool_progress`
- `text`
- `chart`
- `table`
- `dashboard`
- `keepalive`
- `error`
- `final`

## Payload do evento `final`
Campos obrigatorios:
- `type=final`
- `done=true`
- `request_id`

Campos opcionais conforme o fluxo:
- `source`
- `confidence`
- `mode`
- `citations`
- `image_asset`
- `audio_asset`
- `automation_request`

## Estados de automacao suportados
- `pending_user_approval`
- `draft_ready`
- `completed`
- `rejected`

## Politica de capability
- `memory` controla historico persistente e recuperacao cross-session.
- `multimodal` e o master switch de `attachments` e `voice`.
- `computer_use` controla automacoes aprovadas no chat.

## Triage de suporte

### Historico nao aparece
- Validar `GET /api/v1/chat/capabilities?debug=true`.
- Confirmar `memory.active=true`.

### Anexo, microfone ou voz sumiram
- Conferir `multimodal.active`.
- Conferir `attachments.active` ou `voice.active`.

### Automacao bloqueada
- Conferir `computer_use.active`.
- Validar `GET /api/v1/chat/automation/history`.
- Se a acao for sensivel, exigir aprovacao explicita antes de reprocessar.

### Citacoes nao vieram
- Revisar o payload `final`.
- Confirmar se a resposta veio por caminho fundamentado e se `citations` foi emitido pelo backend.

## Evidencias de suporte
- `request_id` da conversa.
- `session_id` da sessao.
- payload de `GET /api/v1/chat/capabilities?debug=true`.
- screenshot ou export do card de automacao, quando aplicavel.
