# Relatório de Segurança - Caculinha_BI

## Resumo Executivo

O sistema **não pode ser considerado seguro o suficiente para exposição ampla** no estado atual. A arquitetura já tem vários controles úteis, mas o repositório ainda contém falhas de alto impacto que aumentam muito o risco de comprometimento por atacante externo ou por usuário tentando burlar o sistema.

Os pontos mais urgentes são:

1. **segredos reais expostos no repositório e no `.env` local**
2. **superfícies públicas de documentação e configuração excessivamente expostas**
3. **tokens do frontend armazenados em `sessionStorage`, o que amplia o impacto de qualquer XSS**
4. **modelo de autenticação com fallback implícito para `guest/anonymous`, que aumenta risco de rota esquecida sem proteção**
5. **controles de senha e compartilhamento público ainda abaixo do nível ideal**

Este relatório combina revisão do código local com referências atuais de segurança, principalmente OWASP, FastAPI e Starlette.

## Referências externas usadas

- OWASP Authentication Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- OWASP Secrets Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- OWASP Session Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- OWASP HTML5 Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html
- OWASP DOM based XSS Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html
- OWASP File Upload Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
- OWASP API Security Top 10: https://owasp.org/API-Security/editions/2019/en/0x00-header/
- FastAPI OAuth2/JWT security docs: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- Starlette release notes: https://www.starlette.io/release-notes/

## Achados Críticos

### SEC-001 - Segredos reais e credenciais sensíveis expostos no repositório

- Severidade: Crítica
- Impacto: comprometimento direto de banco, provedores LLM, Supabase e integrações externas se alguém tiver acesso ao repositório, backup, máquina ou histórico Git.
- Evidência:
  - `backend/.env:35`
  - `backend/.env:67`
  - `backend/.env:77`
  - `backend/.env:78`
  - `backend/.env:79`
  - `backend/.env:91`
- Detalhe:
  - há senha do SQL Server em texto claro
  - há `GROQ_API_KEY`
  - há `SUPABASE_ANON_KEY`
  - há `SUPABASE_SERVICE_ROLE_KEY`
  - há `SERPAPI_API_KEY`
- Risco prático:
  - invasor pode consumir APIs pagas
  - invasor pode escalar para ações administrativas no Supabase
  - invasor pode acessar ou corromper dados
- Correção recomendada:
  - remover segredos do repositório imediatamente
  - rotacionar todas as chaves expostas
  - usar secret manager/variáveis de ambiente no servidor
  - adicionar secret scanning no CI
- Mitigação adicional:
  - revisar histórico Git e invalidar qualquer credencial já commitada

### SEC-002 - O sistema expõe `/docs`, `/redoc` e `/openapi.json` como rotas públicas

- Severidade: Alta
- Impacto: facilita enumeração de rotas, parâmetros, payloads e superfícies administrativas por atacante.
- Evidência:
  - `backend/main.py:161`
  - `backend/main.py:162`
  - `backend/app/api/middleware/auth.py:35`
  - `backend/app/api/middleware/auth.py:40`
  - `backend/app/api/middleware/auth.py:41`
  - `backend/app/api/middleware/auth.py:42`
- Detalhe:
  - a aplicação publica documentação interativa por padrão
  - o middleware trata essas rotas como públicas
- Referência:
  - o guia de segurança de FastAPI recomenda desabilitar ou proteger docs/OpenAPI em produção
- Correção recomendada:
  - em produção, usar `docs_url=None`, `redoc_url=None`, `openapi_url=None`
  - ou proteger essas rotas com autenticação/admin + allowlist de rede

### SEC-003 - CORS permissivo com fallback `*` e ausência visível de validação de Host confiável

- Severidade: Alta
- Impacto: aumenta risco de configuração incorreta em produção, abuso por origens não previstas e ataques de host header/surface probing.
- Evidência:
  - `backend/main.py:171`
  - `backend/main.py:173`
  - `backend/main.py:174`
  - `backend/main.py:175`
  - `backend/main.py:176`
- Detalhe:
  - `allow_origins=os.getenv("CORS_ORIGINS", "*").split(",")`
  - `allow_credentials=True`
  - não há evidência de `TrustedHostMiddleware`
- Referência:
  - CORS não é autenticação
  - Starlette/FastAPI recomendam configuração explícita e estrita
- Correção recomendada:
  - falhar o startup em produção se `CORS_ORIGINS` estiver vazio ou em `*`
  - adicionar `TrustedHostMiddleware` com lista explícita de hosts
  - separar config de dev e prod

## Achados Altos

### SEC-004 - Tokens e refresh tokens guardados em `sessionStorage`

- Severidade: Alta
- Impacto: qualquer XSS bem-sucedido pode roubar token de acesso e refresh token da sessão atual.
- Evidência:
  - `frontend-solid/src/store/auth.ts:74`
  - `frontend-solid/src/store/auth.ts:75`
  - `frontend-solid/src/store/auth.ts:139`
  - `frontend-solid/src/store/auth.ts:140`
  - `frontend-solid/src/pages/Chat.tsx:547`
  - `frontend-solid/src/pages/Chat.tsx:1344`
- Referência:
  - OWASP Session Management Cheat Sheet
  - OWASP HTML5 Security Cheat Sheet
- Observação:
  - `sessionStorage` é melhor que `localStorage` para duração, mas continua acessível por JavaScript
- Correção recomendada:
  - migrar para cookie `HttpOnly` + `Secure` + `SameSite` com backend/BFF
  - se mantiver bearer token no browser, reduzir TTL, usar rotação agressiva e CSP forte

### SEC-005 - Middleware de autenticação segue a requisição como `guest` quando não há token

- Severidade: Alta
- Impacto: qualquer rota esquecida sem dependency explícita pode ficar acessível indevidamente.
- Evidência:
  - `backend/app/api/middleware/auth.py:79`
  - `backend/app/api/middleware/auth.py:80`
  - `backend/app/api/middleware/auth.py:81`
  - `backend/app/api/middleware/auth.py:82`
  - `backend/app/api/middleware/auth.py:83`
- Detalhe:
  - sem token, o middleware não rejeita; ele injeta `anonymous/default/guest`
- Referência:
  - FastAPI recomenda autenticação explícita e consistente por dependências/routers protegidos
- Correção recomendada:
  - adotar default-deny por router
  - deixar públicas apenas rotas explicitamente allowlisted
  - revisar todas as rotas que hoje dependem de `request.state.user_*`

### SEC-006 - Endpoint de compartilhamento público aceita payload arbitrário do cliente e publica link acessível sem autenticação

- Severidade: Alta
- Impacto: um usuário autenticado pode publicar qualquer conteúdo arbitrário em link público, inclusive material sensível, enganoso ou malicioso.
- Evidência:
  - `backend/app/api/v1/endpoints/shared.py:47`
  - `backend/app/api/v1/endpoints/shared.py:49`
  - `backend/app/api/v1/endpoints/shared.py:56`
  - `backend/app/api/v1/endpoints/shared.py:67`
  - `backend/app/api/v1/endpoints/shared.py:72`
  - `backend/app/api/v1/endpoints/shared.py:89`
  - `backend/app/api/v1/endpoints/shared.py:97`
- Detalhe:
  - o backend não recarrega a conversa original a partir de ownership
  - ele aceita `messages` enviados pelo cliente e cria o link
  - o endpoint público retorna o conteúdo a qualquer pessoa com o `share_id`
- Correção recomendada:
  - compartilhar apenas por `session_id` do owner autenticado
  - regenerar o conteúdo no backend
  - limitar tamanho e quantidade de mensagens
  - registrar consentimento explícito e permitir revogação/expiração curta

## Achados Médios

### SEC-007 - Política de senha inconsistente e fraca para mudança de senha

- Severidade: Média
- Impacto: facilita adoção de senhas fracas e reduz resiliência contra credential stuffing e brute force.
- Evidência:
  - `backend/app/schemas/auth.py:29`
  - `backend/app/schemas/auth.py:30`
  - `backend/app/api/v1/endpoints/auth.py:198`
  - `backend/app/api/v1/endpoints/auth.py:222`
  - `backend/app/core/security/input_validator.py:16`
- Detalhe:
  - o schema de login aceita senha com tamanho mínimo `1`
  - o endpoint de troca de senha não chama `validate_password_strength`
  - existe função de validação de força, mas ela não está integrada no fluxo
- Referência:
  - OWASP Authentication Cheat Sheet
  - NIST 800-63B recomenda política moderna, comprimento adequado e bloqueio de senhas comprometidas
- Correção recomendada:
  - exigir comprimento mínimo consistente
  - bloquear senhas vazadas/comuns
  - opcionalmente adotar MFA para perfis privilegiados

### SEC-008 - Endpoint de diagnóstico expõe `DATABASE_URL` completa para o cliente admin

- Severidade: Média
- Impacto: qualquer comprometimento de conta admin passa a expor credenciais de banco pelo próprio endpoint.
- Evidência:
  - `backend/app/api/v1/endpoints/diagnostics.py:166`
  - `backend/app/api/v1/endpoints/diagnostics.py:167`
- Correção recomendada:
  - mascarar usuário/senha no retorno
  - retornar apenas host, database e modo de runtime

### SEC-009 - `/health` raiz expõe detalhes operacionais desnecessários

- Severidade: Média
- Impacto: ajuda enumeração de arquitetura e caminho de dados.
- Evidência:
  - `backend/main.py:236`
  - `backend/main.py:243`
  - `backend/main.py:244`
  - `backend/main.py:245`
  - `backend/main.py:246`
- Correção recomendada:
  - retornar payload mínimo em endpoint público
  - mover detalhes de runtime para rota autenticada de diagnóstico

### SEC-010 - Há scripts e testes com credenciais de exemplo ou administrativas no repositório

- Severidade: Média
- Impacto: incentiva uso indevido em ambientes reais, reduz higiene operacional e pode causar reutilização perigosa.
- Evidência:
  - `backend/fix_admin_complete.py:26`
  - `backend/fix_admin_password.py:16`
  - `backend/scripts/load_data.py:30`
  - `backend/scripts/diagnostico_auth.py:159`
  - `frontend-solid/tests/integration/setup.ts:19`
  - `frontend-solid/tests/integration/setup.ts:24`
- Correção recomendada:
  - mover tudo para fixtures claramente artificiais
  - padronizar placeholders não reutilizáveis
  - revisar scripts operacionais antes de uso em produção

## Controles Positivos Já Visíveis

- validação e saneamento de anexos/nomes de arquivo e bloqueio de conteúdo ativo:
  - `backend/app/core/security/content_safety.py:113`
  - `backend/app/core/security/content_safety.py:130`
  - `backend/app/api/v1/endpoints/ingest.py:123`
  - `backend/app/api/v1/endpoints/ingest.py:145`
- limite de tamanho em upload textual e imagem:
  - `backend/app/api/v1/endpoints/ingest.py:30`
  - `backend/app/api/v1/endpoints/ingest.py:31`
- lock de runtime para ingestão concorrente:
  - `backend/app/api/v1/endpoints/ingest.py:196`
- tokens SSE opacos e curtos:
  - `backend/app/api/dependencies.py:26`
  - `backend/app/api/dependencies.py:104`
  - `backend/app/api/dependencies.py:121`
- guardrails semânticos para impedir respostas incoerentes:
  - `backend/app/core/utils/response_validator.py`

## Prioridade de Correção

### Corrigir imediatamente

1. remover e rotacionar todos os segredos do repositório
2. fechar `/docs`, `/redoc`, `/openapi.json` em produção
3. endurecer CORS e adicionar `TrustedHostMiddleware`
4. eliminar fallback silencioso para `guest` em rotas protegidas

### Próxima onda

5. migrar tokens do frontend para cookie `HttpOnly`
6. endurecer compartilhamento público de conversas
7. padronizar política de senha e MFA para admins
8. mascarar dados sensíveis em health/diagnostics

### Depois da homologação inicial

9. ativar secret scanning e dependency scanning no CI
10. adicionar CSP forte e revisar superfícies de XSS no frontend
11. adicionar monitoramento de abuso, brute force e comportamento anômalo
12. revisar bibliotecas e advisories de FastAPI/Starlette periodicamente

## Conclusão

O sistema tem base boa para endurecimento, mas **ainda não está em nível “seguro para exposição ampla”** sem correções de segredos, autenticação padrão, superfícies públicas e armazenamento de token no frontend.

O ponto mais urgente é operacional: **assumir que os segredos atuais já estão comprometidos e rotacioná-los**.
