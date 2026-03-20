# ChatBI Capability Rollout Runbook

## Objetivo
Operar, habilitar, desabilitar e diagnosticar as capacidades sensiveis do ChatBI com baixo retrabalho e rollback claro.

## Capacidades cobertas
- `memory`
- `multimodal` (master switch)
- `attachments`
- `voice`
- `computer_use`

## Mapa de flags

### Memory
- `CHAT_CAPABILITY_MEMORY_ENABLED`
- `CHAT_CAPABILITY_MEMORY_ALLOWED_ROLES`
- `CHAT_CAPABILITY_MEMORY_ALLOWED_USERS`

### Multimodal master
- `CHAT_CAPABILITY_MULTIMODAL_ENABLED`
- `CHAT_CAPABILITY_MULTIMODAL_ALLOWED_ROLES`
- `CHAT_CAPABILITY_MULTIMODAL_ALLOWED_USERS`

### Attachments
- `CHAT_CAPABILITY_ATTACHMENTS_ENABLED`
- `CHAT_CAPABILITY_ATTACHMENTS_ALLOWED_ROLES`
- `CHAT_CAPABILITY_ATTACHMENTS_ALLOWED_USERS`

### Voice
- `CHAT_CAPABILITY_VOICE_ENABLED`
- `CHAT_CAPABILITY_VOICE_ALLOWED_ROLES`
- `CHAT_CAPABILITY_VOICE_ALLOWED_USERS`

### Computer use
- `CHAT_CAPABILITY_COMPUTER_USE_ENABLED`
- `CHAT_CAPABILITY_COMPUTER_USE_ALLOWED_ROLES`
- `CHAT_CAPABILITY_COMPUTER_USE_ALLOWED_USERS`

## Regras operacionais
- `multimodal` e o master switch. Se estiver `false`, `attachments` e `voice` ficam inativos mesmo quando suas flags locais estiverem liberadas.
- `attachments` controla ingestao de arquivo e imagem.
- `voice` controla entrada por microfone e leitura por voz.
- `memory` controla historico persistido, reopen/delete de conversa e recuperacao cross-session.
- `computer_use` fica desabilitado por padrao e deve ser liberado apenas em rollout controlado.

## Habilitar e desabilitar

### Piloto de memoria para analistas e viewers
- `CHAT_CAPABILITY_MEMORY_ENABLED=true`
- `CHAT_CAPABILITY_MEMORY_ALLOWED_ROLES=admin,analyst,viewer`
- `CHAT_CAPABILITY_MEMORY_ALLOWED_USERS=`

### Piloto de anexos somente para analistas
- `CHAT_CAPABILITY_MULTIMODAL_ENABLED=true`
- `CHAT_CAPABILITY_MULTIMODAL_ALLOWED_ROLES=admin,analyst`
- `CHAT_CAPABILITY_ATTACHMENTS_ENABLED=true`
- `CHAT_CAPABILITY_ATTACHMENTS_ALLOWED_ROLES=analyst`
- `CHAT_CAPABILITY_ATTACHMENTS_ALLOWED_USERS=`

### Piloto de voz para usuarios nomeados
- `CHAT_CAPABILITY_MULTIMODAL_ENABLED=true`
- `CHAT_CAPABILITY_VOICE_ENABLED=true`
- `CHAT_CAPABILITY_VOICE_ALLOWED_ROLES=`
- `CHAT_CAPABILITY_VOICE_ALLOWED_USERS=usuario.voice@example.com`

### Bloqueio imediato de anexos
- `CHAT_CAPABILITY_ATTACHMENTS_ENABLED=false`

### Bloqueio imediato de voz
- `CHAT_CAPABILITY_VOICE_ENABLED=false`

### Bloqueio imediato de computer use
- `CHAT_CAPABILITY_COMPUTER_USE_ENABLED=false`

## Diagnostico rapido

### Usuario atual
- `GET /api/v1/chat/capabilities`
- `GET /api/v1/chat/capabilities?debug=true`

### Simulacao administrativa
- Requer role `admin`.
- Exemplo:
  - `GET /api/v1/chat/capabilities?debug=true&role=viewer&username=piloto.viewer&email=piloto.viewer@example.com&user_id=viewer-1`

### Leitura do payload
- `capabilities`: matriz final efetiva.
- `diagnostics.<capability>.enabled`: flag global/local carregada do ambiente.
- `diagnostics.<capability>.allowed_by_role`: liberada pela role.
- `diagnostics.<capability>.allowed_by_user`: liberada por allowlist nominal.
- `diagnostics.<capability>.missing_requires`: dependencias ausentes, por exemplo `attachments -> multimodal`.
- `diagnostics.<capability>.active`: estado final aplicado.

## Troubleshooting

### Historico nao aparece
- Verificar `memory.active` em `/api/v1/chat/capabilities?debug=true`.
- Se `enabled=true` e `active=false`, revisar role/allowlist.

### Botao de anexo sumiu
- Verificar `attachments.active`.
- Se `attachments.enabled=true` mas `missing_requires=["multimodal"]`, religar o master switch multimodal.

### Microfone e leitura por voz sumiram
- Verificar `voice.active`.
- Se `voice.enabled=true` mas `missing_requires=["multimodal"]`, religar `multimodal`.

### Computer use continua bloqueado
- Verificar `computer_use.active`.
- Confirmar rollout explicito por role ou usuario.
- Manter default `false` fora de pilotos aprovados.

## Rollback
- Voltar a flag local para `false`.
- Se o bloqueio precisar atingir todas as experiencias ricas de uma vez, usar `CHAT_CAPABILITY_MULTIMODAL_ENABLED=false`.
- Revalidar com `GET /api/v1/chat/capabilities?debug=true`.

## Evidencias minimas
- Print ou payload do endpoint de diagnostico antes e depois da mudanca.
- Registro das flags alteradas.
- Resultado dos testes alvo de `capabilities`, `chat history`, `ingest` e `Chat.tsx`.
