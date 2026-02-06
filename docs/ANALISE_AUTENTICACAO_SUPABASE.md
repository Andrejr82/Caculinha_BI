# Análise Profunda - Problema de Autenticação Supabase

## 🔍 Diagnóstico Completo

**Data:** 2026-01-01  
**Problema:** Erro ao tentar fazer login com `admin@agentbi.com` / `admin123`

---

## 📊 Resultados da Análise

### 1. Status dos Sistemas de Autenticação

| Sistema | Status | Observações |
|---------|--------|-------------|
| **Supabase Auth** | ⚠️ Configurado | Usuário pode não existir ou senha incorreta |
| **Parquet (users.parquet)** | ✅ Funcionando | 2 usuários encontrados, incluindo admin |
| **SQL Server** | ❌ Não disponível | Conexão falhando (conforme diagnóstico anterior) |

### 2. Usuários Encontrados no Parquet

```
Total: 2 usuários

1. Username: admin
   Email: admin@agentbi.com
   Role: admin
   Ativo: True
   Senha: INCORRETA (hash não corresponde a 'admin123')

2. Username: user
   Email: user@agentbi.com
   Role: user
   Ativo: True
```

### 3. Fluxo de Autenticação Atual

De acordo com `auth_service.py`, a ordem de prioridade é:

```
1. Supabase Auth (se USE_SUPABASE_AUTH=true)
   ↓ (se falhar)
2. Parquet (fallback)
   ↓ (se falhar)
3. SQL Server (se USE_SQL_SERVER=true e db disponível)
```

---

## 🎯 Problemas Identificados

### Problema 1: Senha Incorreta no Parquet
- O hash da senha armazenado em `users.parquet` **NÃO corresponde** a `admin123`
- Quando Supabase falha, o fallback para Parquet também falha

### Problema 2: Usuário Pode Não Existir no Supabase
- Não foi possível confirmar se o usuário existe no Supabase Auth
- Requer `SUPABASE_SERVICE_ROLE_KEY` para verificar

### Problema 3: Configuração Híbrida Complexa
- Sistema configurado para usar Supabase como primário
- Mas fallback para Parquet não funciona devido à senha incorreta

---

## ✅ Soluções (em ordem de facilidade)

### SOLUÇÃO 1: Usar Apenas Parquet (MAIS RÁPIDA) ⭐ RECOMENDADO

Esta é a solução mais simples e rápida!

**Passo 1:** Recriar o usuário admin no Parquet com senha correta

```bash
cd backend
python scripts/create_admin_user.py
```

Ou manualmente, execute este script Python:

```python
import bcrypt
import duckdb
import uuid
from pathlib import Path

# Gera hash da senha
password = "admin123"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Atualiza o usuario admin
parquet_path = Path("backend/data/parquet/users.parquet")

conn = duckdb.connect()

# Le o arquivo atual
df = conn.execute(f"SELECT * FROM read_parquet('{parquet_path}')").df()

# Atualiza a senha do admin
df.loc[df['username'] == 'admin', 'hashed_password'] = hashed

# Salva de volta
conn.execute(f"COPY df TO '{parquet_path}' (FORMAT PARQUET)")
conn.close()

print("Senha do admin atualizada com sucesso!")
```

**Passo 2:** Configurar `.env` para usar Parquet

```env
# Desabilitar Supabase
USE_SUPABASE_AUTH=false

# Habilitar fallback para Parquet
FALLBACK_TO_PARQUET=true

# Desabilitar SQL Server (já está falhando)
USE_SQL_SERVER=false
```

**Passo 3:** Reiniciar o backend

```bash
# Se estiver usando Docker
docker-compose restart backend

# Se estiver rodando localmente
# Pare o backend (Ctrl+C) e inicie novamente
```

**Vantagens:**
- ✅ Solução imediata
- ✅ Sem dependência de serviços externos
- ✅ Mais rápido para desenvolvimento
- ✅ Dados já estão no Parquet

---

### SOLUÇÃO 2: Configurar Supabase Corretamente

Se você realmente precisa usar Supabase:

**Passo 1:** Obter a Service Role Key

1. Acesse: https://supabase.com/dashboard
2. Selecione seu projeto
3. Settings → API
4. Copie a **service_role** key (NÃO a anon key!)

**Passo 2:** Configurar no `.env`

```env
SUPABASE_SERVICE_ROLE_KEY=sua_service_role_key_aqui
```

**Passo 3:** Criar o usuário admin no Supabase

```bash
cd backend
python create_admin_supabase.py
```

Este script irá:
- Verificar se o usuário já existe
- Criar o usuário `admin@agentbi.com` com senha `admin123`
- Auto-confirmar o email
- Criar o perfil na tabela `user_profiles`

**Passo 4:** Configurar `.env` para usar Supabase

```env
USE_SUPABASE_AUTH=true
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=sua_anon_key
SUPABASE_SERVICE_ROLE_KEY=sua_service_role_key
```

**Passo 5:** Testar a autenticação

```bash
python diagnose_supabase_auth.py
```

---

### SOLUÇÃO 3: Criar Tabela user_profiles no Supabase

Se você está usando Supabase mas não tem a tabela `user_profiles`:

**SQL para criar a tabela:**

```sql
-- Criar tabela user_profiles
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Habilitar RLS (Row Level Security)
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Política: Usuários podem ler seu próprio perfil
CREATE POLICY "Users can read own profile"
    ON public.user_profiles
    FOR SELECT
    USING (auth.uid() = id);

-- Política: Service role pode fazer tudo
CREATE POLICY "Service role can do everything"
    ON public.user_profiles
    FOR ALL
    USING (auth.role() = 'service_role');

-- Inserir usuário admin
INSERT INTO public.user_profiles (id, username, role, is_active)
VALUES (
    'ID_DO_USUARIO_ADMIN_AQUI',  -- Substitua pelo ID do usuário criado no Auth
    'admin',
    'admin',
    true
);
```

Execute este SQL no **SQL Editor** do Supabase Dashboard.

---

## 🔧 Scripts Criados para Diagnóstico

Foram criados 4 scripts para ajudar:

### 1. `diagnose_supabase_auth.py`
Diagnóstico completo da autenticação Supabase

```bash
python diagnose_supabase_auth.py
```

**O que faz:**
- Verifica configuração do .env
- Testa conexão com Supabase
- Verifica se usuário existe
- Testa autenticação
- Lista usuários (se tiver service key)
- Testa AuthService da aplicação

### 2. `create_admin_supabase.py`
Cria usuário admin no Supabase Auth

```bash
python create_admin_supabase.py
```

**O que faz:**
- Verifica se usuário já existe
- Cria usuário `admin@agentbi.com`
- Auto-confirma email
- Cria perfil na tabela `user_profiles`

### 3. `check_parquet_users.py`
Verifica usuários no arquivo Parquet

```bash
python check_parquet_users.py
```

**O que faz:**
- Lista todos os usuários no Parquet
- Verifica se admin existe
- Testa a senha `admin123`

### 4. `test_db_connections_html.py`
Testa todas as conexões (já executado anteriormente)

```bash
python test_db_connections_html.py
```

---

## 📋 Checklist de Verificação

Use este checklist para resolver o problema:

### Opção A: Usar Parquet (Recomendado)

- [ ] Executar `python check_parquet_users.py` para verificar usuários
- [ ] Recriar usuário admin com senha correta
- [ ] Editar `backend/.env`:
  - [ ] `USE_SUPABASE_AUTH=false`
  - [ ] `FALLBACK_TO_PARQUET=true`
  - [ ] `USE_SQL_SERVER=false`
- [ ] Reiniciar backend
- [ ] Testar login com `admin` / `admin123`

### Opção B: Usar Supabase

- [ ] Obter `SUPABASE_SERVICE_ROLE_KEY`
- [ ] Adicionar ao `backend/.env`
- [ ] Executar `python create_admin_supabase.py`
- [ ] Executar `python diagnose_supabase_auth.py` para verificar
- [ ] Editar `backend/.env`:
  - [ ] `USE_SUPABASE_AUTH=true`
- [ ] Reiniciar backend
- [ ] Testar login com `admin@agentbi.com` / `admin123`

---

## 🎓 Entendendo o Código de Autenticação

### Fluxo no `auth_service.py`

```python
async def authenticate_user(username, password):
    # 1. Tenta Supabase (se habilitado)
    if USE_SUPABASE_AUTH:
        user = await _auth_from_supabase(username, password)
        if user:
            return user  # ✅ Sucesso
    
    # 2. Fallback para Parquet
    user = await _auth_from_parquet(username, password)
    if user:
        return user  # ✅ Sucesso
    
    # 3. Tenta SQL Server (se habilitado)
    if USE_SQL_SERVER and db:
        user = await _auth_from_sql(username, password, db)
        if user:
            return user  # ✅ Sucesso
    
    # ❌ Falhou em todos
    return None
```

### Problema Atual

```
1. Supabase → ❌ Usuário não existe ou senha incorreta
   ↓
2. Parquet → ❌ Senha incorreta (hash não corresponde)
   ↓
3. SQL Server → ❌ Não disponível (conexão falhando)
   ↓
RESULTADO: Login falha
```

### Solução

```
Opção 1 (Parquet):
1. Corrigir senha no Parquet → ✅
2. Desabilitar Supabase
3. Login funciona via Parquet

Opção 2 (Supabase):
1. Criar usuário no Supabase → ✅
2. Login funciona via Supabase
3. Parquet como fallback
```

---

## 💡 Recomendação Final

**Como desenvolvedor sênior, recomendo:**

### ⭐ Use a SOLUÇÃO 1 (Parquet)

**Motivos:**

1. **Mais simples** - Sem dependência de serviços externos
2. **Mais rápido** - Autenticação local é instantânea
3. **Mais confiável** - Sem problemas de rede ou API
4. **Desenvolvimento** - Ideal para ambiente de desenvolvimento
5. **Já funciona** - Supabase e DuckDB já estão OK

### Quando usar Supabase?

Use Supabase Auth apenas se:
- Precisar de autenticação distribuída (múltiplos servidores)
- Precisar de features como OAuth, MFA, etc.
- Estiver em produção com múltiplos usuários
- Precisar de gestão de usuários via dashboard

### Arquitetura Recomendada

```
Desenvolvimento:
  - USE_SUPABASE_AUTH=false
  - Autenticação via Parquet
  - Rápido e simples

Produção:
  - USE_SUPABASE_AUTH=true
  - Autenticação via Supabase
  - Parquet como fallback
  - Mais robusto e escalável
```

---

## 📞 Próximos Passos

**Escolha uma opção e execute:**

### OPÇÃO A - Parquet (5 minutos)

```bash
# 1. Verificar usuários
cd backend
python check_parquet_users.py

# 2. Recriar admin (se necessário)
python scripts/create_admin_user.py

# 3. Editar .env
# USE_SUPABASE_AUTH=false
# FALLBACK_TO_PARQUET=true

# 4. Reiniciar backend
```

### OPÇÃO B - Supabase (15 minutos)

```bash
# 1. Obter Service Role Key do dashboard

# 2. Adicionar ao .env
# SUPABASE_SERVICE_ROLE_KEY=...

# 3. Criar usuário admin
cd backend
python create_admin_supabase.py

# 4. Testar
python diagnose_supabase_auth.py

# 5. Editar .env
# USE_SUPABASE_AUTH=true

# 6. Reiniciar backend
```

---

## 🐛 Troubleshooting

### Erro: "Invalid login credentials"
- **Causa:** Usuário não existe no Supabase ou senha incorreta
- **Solução:** Execute `create_admin_supabase.py`

### Erro: "User not found in Parquet"
- **Causa:** Usuário não existe no arquivo users.parquet
- **Solução:** Execute script para criar admin no Parquet

### Erro: "Invalid password"
- **Causa:** Hash da senha não corresponde
- **Solução:** Recrie o usuário com a senha correta

### Erro: "Supabase client not configured"
- **Causa:** SUPABASE_URL ou SUPABASE_ANON_KEY não configurados
- **Solução:** Configure no .env ou desabilite Supabase

---

**Documentação criada em:** 2026-01-01  
**Versão:** 1.0  
**Autor:** Diagnóstico Automático de Autenticação
