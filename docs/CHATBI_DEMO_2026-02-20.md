# ChatBI - Roteiro de Demonstração (Sexta-feira, 20/02/2026)

## Objetivo da demo
Mostrar o sistema funcionando ponta a ponta para o negócio, com foco em:
- Perguntas livres em linguagem natural.
- Respostas com texto, tabela e gráfico.
- Segurança (stream com token efêmero).
- Governança por perfil (role dinâmica no chat).

## Pré-demo (checklist rápido)
- Backend iniciado sem erro.
- Frontend iniciado sem erro.
- Login com usuário de demonstração válido.
- Arquivo Parquet carregado e consultas respondendo.
- Endpoint `/api/v1/chat/stream-token` retornando `200`.
- Stream em `/api/v1/chat/stream` funcionando com `stream_token`.
- Exportação da conversa (JSON/Markdown/TXT) funcionando.
- Feedback (`👍/👎`) funcionando sem erro 500.

Checklist detalhado:
- `docs/CHATBI_CHECKLIST_PRE_DEMO_2026-02-20.md`

## Script sugerido (15-20 minutos)
1. Abertura (2 min)
- Contexto: ChatBI para suporte ao time comercial/compras.
- Resultado esperado: reduzir tempo entre pergunta e ação.

2. Segurança e acesso (3 min)
- Mostrar login.
- Mostrar que o chat abre stream com `stream_token` (sem JWT na URL).
- Explicar controle por perfil (role dinâmica no backend).

3. Perguntas livres (5 min)
- Exemplo 1: "Como estão as vendas por UNE na última janela?"
- Exemplo 2: "Mostre os itens com maior risco de ruptura."
- Exemplo 3: "Quais categorias com maior margem e menor giro?"

4. Saídas úteis para operação (4 min)
- Resposta textual com contexto.
- Tabela operacional para tomada de decisão.
- Gráfico para leitura executiva.
- Exportar conversa para documentação.

5. Encerramento (2-3 min)
- Reforçar status atual do plano e próximos passos.
- Mostrar matriz de go-live (`docs/CHATBI_GO_LIVE_MATRIZ.md`).

## Perguntas de contingência (se algo falhar)
- Se LLM falhar: mostrar fallback e mensagem amigável.
- Se latência subir: usar pergunta simples preparada.
- Se ferramenta específica falhar: demonstrar outro fluxo (consulta + gráfico).

## Plano B (demo segura)
- Ter 3 perguntas “curinga” já testadas no ambiente.
- Manter uma sessão já aquecida no navegador.
- Manter print/log de evidência das implementações críticas.

## Evidências técnicas para citar na apresentação
- Role dinâmica por usuário no chat:
  - `backend/app/services/chat_service_v3.py`
  - `backend/app/api/v1/endpoints/chat.py`
- Stream token efêmero obrigatório:
  - `backend/app/api/dependencies.py`
  - `backend/app/api/v1/endpoints/chat.py`
  - `frontend-solid/src/pages/Chat.tsx`
- Feedback funcional:
  - `frontend-solid/src/pages/Chat.tsx`
  - `backend/app/api/v1/endpoints/chat.py`

## Melhorias concluídas para esta demo
- Stream seguro no ChatBI com token efêmero obrigatório.
- Token efêmero com reuso limitado (3 usos, 120s) para robustez em reconexão SSE.
- Role dinâmica no ChatBI (sem hardcode fixo no processamento).
- Normalização de perfil para manter capacidade de uso por perfis de negócio (`user/compras/coordenador -> analyst` no escopo de tools).
- Feedback de resposta (`👍/👎`) funcional sem erro 500.

## Mensagem final sugerida
"Hoje o ChatBI já opera com fluxo conversacional robusto, segurança de stream endurecida, e trilha clara para go-live enterprise conforme a matriz priorizada."
