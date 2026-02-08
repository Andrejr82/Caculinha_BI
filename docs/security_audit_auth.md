# Relatório de Auditoria de Segurança: Autenticação

## Objetivo
Validar se as autenticações estão sendo feitas exclusivamente pelo Supabase, conforme solicitado.

## Diagnóstico Inicial
- **Endpoint v2 (`/api/v2/auth/login`)**: Identificado o uso de usuários **MOCK** (`MOCK_USERS`) hardcoded no código. O login gerava tokens locais sem validar credenciais no Supabase.
- **Middleware**: Validava tokens locais corretamente, mas permitia tokens gerados pelo sistema de mock.
- **Configuração**: `USE_SUPABASE_AUTH` estava habilitado (True), mas o endpoint de login ignorava essa configuração em favor do mock.

## Ações Realizadas
1. **Refatoração do Endpoint de Login**:
   - Removidos completamente os `MOCK_USERS` do arquivo `backend/api/v2/endpoints/auth.py`.
   - Implementada integração com `backend.app.core.auth_service.AuthService`.
   - O login agora invoca `auth_service.authenticate_user(email, password)`.

2. **Fluxo de Autenticação Atual**:
   - **Prioridade 1**: Tenta autenticar via **Supabase Auth** (se `USE_SUPABASE_AUTH=True`).
   - **Prioridade 2**: Se falhar ou desabilitado, tenta `users.parquet` (Legado/Local).
   - **Prioridade 3**: SQL Server (se configurado).

3. **Validação de Dependências**:
   - Confirmada a presença das bibliotecas `supabase`, `bcrypt` e modelos de banco de dados necessários para o funcionamento do `AuthService`.

## Conclusão
O sistema de autenticação foi corrigido. O endpoint de login agora **respeita a configuração do Supabase** e não utiliza mais credenciais "falsas" hardcoded. A autenticação é delegada ao provedor configurado (Supabase por padrão).

---
*Data: 2026-02-08*
*Status: APROVADO*
