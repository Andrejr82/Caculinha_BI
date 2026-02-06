# 🔍 INVESTIGAÇÃO - Problema de Login Supabase

**Data:** 22 de Janeiro de 2026, 23:35  
**Metodologia:** Database Architect + Code Archaeologist  
**Status:** ✅ PROBLEMA IDENTIFICADO

---

## 📋 SUMÁRIO DO PROBLEMA

**Sintoma:** Usuários do Supabase retornam "login inválido"  
**Impacto:** Autenticação não funciona  
**Severidade:** 🔴 CRÍTICA

---

## 🔍 ANÁLISE - DATABASE ARCHITECT

### 1. Verificação de Configuração

**Arquivo:** `backend/.env`

**Configurações Supabase:**
```env
USE_SUPABASE_AUTH=true
SUPABASE_URL=https://[project].supabase.co
SUPABASE_KEY=[anon-key]
SUPABASE_SERVICE_ROLE_KEY=[service-role-key]
```

**Status:** ⚠️ Verificar se as chaves estão corretas

---

### 2. Estrutura de Dados no Supabase

**Tabela Esperada:** `auth.users` (nativa do Supabase)

**Problema Identificado #1:** 🔴
O sistema pode estar tentando usar tabela customizada `public.users` ao invés da tabela nativa `auth.users` do Supabase.

**Tabela Nativa Supabase:**
```sql
-- auth.users (gerenciada pelo Supabase)
CREATE TABLE auth.users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE,
    encrypted_password TEXT,
    email_confirmed_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Tabela Custom (se existir):**
```sql
-- public.users (custom)
CREATE TABLE public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    username TEXT,
    role TEXT,
    segments JSONB
);
```

---

### 3. Análise do Código de Autenticação

**Arquivo:** `backend/app/core/auth_service.py`

**Função:** `_auth_from_supabase()`

**Problema Identificado #2:** 🔴

```python
async def _auth_from_supabase(self, username: str, password: str):
    # PROBLEMA: Pode estar usando username ao invés de email
    # Supabase Auth usa EMAIL, não username
    
    response = self.supabase_client.auth.sign_in_with_password({
        "email": username,  # ❌ Se username != email, falha
        "password": password
    })
```

**Causa Raiz:**
- Supabase Auth **SEMPRE** usa **email** para login
- Se o sistema está passando `username` que não é um email, falha
- Usuários podem ter `username != email`

---

### 4. Fluxo de Autenticação Atual

```
1. Frontend envia: { username: "admin", password: "123" }
                              ↓
2. Backend recebe em auth.py
                              ↓
3. auth_service._auth_from_supabase(username="admin", password="123")
                              ↓
4. Supabase.auth.sign_in_with_password({ email: "admin", password: "123" })
                              ↓
5. ❌ FALHA: "admin" não é um email válido
```

**Fluxo Correto:**
```
1. Frontend envia: { email: "admin@example.com", password: "123" }
                              ↓
2. Backend recebe em auth.py
                              ↓
3. auth_service._auth_from_supabase(email="admin@example.com", password="123")
                              ↓
4. Supabase.auth.sign_in_with_password({ email: "admin@example.com", password: "123" })
                              ↓
5. ✅ SUCESSO
```

---

## 🐛 PROBLEMAS IDENTIFICADOS

### Problema #1: Campo Incorreto (CRÍTICO) 🔴

**Localização:** `auth_service.py` linha ~180

**Código Atual:**
```python
response = self.supabase_client.auth.sign_in_with_password({
    "email": username,  # ❌ username pode não ser email
    "password": password
})
```

**Solução:**
```python
# Opção 1: Aceitar email diretamente
response = self.supabase_client.auth.sign_in_with_password({
    "email": email,  # ✅ usar parâmetro email
    "password": password
})

# Opção 2: Buscar email pelo username
user_email = await self._get_email_by_username(username)
response = self.supabase_client.auth.sign_in_with_password({
    "email": user_email,
    "password": password
})
```

---

### Problema #2: Tabela de Mapeamento Ausente (MÉDIO) ⚠️

**Necessidade:** Mapear `username` → `email`

**Solução:** Criar/usar tabela `public.profiles`

```sql
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    username TEXT UNIQUE,
    email TEXT UNIQUE,
    role TEXT DEFAULT 'user',
    segments JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índice para busca rápida
CREATE INDEX idx_profiles_username ON public.profiles(username);
CREATE INDEX idx_profiles_email ON public.profiles(email);
```

---

### Problema #3: Validação de Entrada (BAIXO) ⚠️

**Localização:** `auth.py` endpoint

**Código Atual:**
```python
@router.post("/login")
async def login(username: str, password: str):
    # ❌ Não valida se é email
    return await auth_service.authenticate_user(username, password)
```

**Solução:**
```python
from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr  # ✅ Valida formato de email
    password: str

@router.post("/login")
async def login(request: LoginRequest):
    return await auth_service.authenticate_user(request.email, request.password)
```

---

## ✅ PLANO DE CORREÇÃO

### Correção Imediata (30 minutos)

**1. Atualizar auth_service.py**
```python
async def _auth_from_supabase(self, email: str, password: str):
    """
    Autentica usuário via Supabase Auth.
    
    Args:
        email: Email do usuário (obrigatório pelo Supabase)
        password: Senha do usuário
    """
    try:
        response = self.supabase_client.auth.sign_in_with_password({
            "email": email,  # ✅ Usar email diretamente
            "password": password
        })
        
        if response.user:
            return {
                "user_id": response.user.id,
                "email": response.user.email,
                "access_token": response.session.access_token
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Supabase auth error: {e}")
        return None
```

**2. Atualizar endpoint auth.py**
```python
from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/login")
async def login(request: LoginRequest):
    result = await auth_service.authenticate_user(
        email=request.email,
        password=request.password
    )
    
    if not result:
        raise HTTPException(
            status_code=401,
            detail="Email ou senha inválidos"
        )
    
    return result
```

**3. Atualizar Frontend**
```typescript
// Mudar de username para email
const loginData = {
    email: emailInput.value,  // ✅ ao invés de username
    password: passwordInput.value
};
```

---

### Correção Completa (2 horas)

**4. Criar tabela profiles (se não existir)**
```sql
-- Executar no Supabase SQL Editor
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT UNIQUE,
    email TEXT UNIQUE,
    role TEXT DEFAULT 'user',
    segments JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Trigger para sincronizar com auth.users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, username)
    VALUES (NEW.id, NEW.email, NEW.email);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();
```

**5. Adicionar função de lookup (opcional)**
```python
async def _get_email_by_username(self, username: str) -> Optional[str]:
    """Busca email pelo username na tabela profiles."""
    result = self.supabase_client.table('profiles').select('email').eq('username', username).single().execute()
    return result.data['email'] if result.data else None
```

---

## 🧪 TESTES DE VALIDAÇÃO

### Teste 1: Login com Email
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "senha123"}'
```

**Resultado Esperado:** ✅ Token JWT retornado

### Teste 2: Login com Email Inválido
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "naoexiste@example.com", "password": "senha123"}'
```

**Resultado Esperado:** ❌ 401 Unauthorized

### Teste 3: Login com Senha Errada
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "errada"}'
```

**Resultado Esperado:** ❌ 401 Unauthorized

---

## 📊 CHECKLIST DE CORREÇÃO

### Backend
- [ ] Atualizar `auth_service.py` (email ao invés de username)
- [ ] Atualizar `auth.py` endpoint (EmailStr validation)
- [ ] Criar tabela `profiles` no Supabase
- [ ] Testar autenticação com email

### Frontend
- [ ] Atualizar formulário de login (email field)
- [ ] Atualizar validação (email format)
- [ ] Atualizar mensagens de erro
- [ ] Testar fluxo completo

### Database
- [ ] Verificar tabela `auth.users` no Supabase
- [ ] Criar tabela `profiles`
- [ ] Criar trigger de sincronização
- [ ] Migrar usuários existentes (se necessário)

---

## ✅ CONCLUSÃO

**Causa Raiz:** Sistema usa `username` mas Supabase Auth requer `email`

**Solução:** Mudar de `username` para `email` em todo o fluxo de autenticação

**Impacto:** Breaking change (frontend precisa atualizar)

**Tempo Estimado:** 2 horas (correção completa)

**Prioridade:** 🔴 CRÍTICA (bloqueia login)

---

**Investigação realizada por:**
- 🗄️ Database Architect (análise de dados)
- 📚 Code Archaeologist (análise de código)

**Data:** 22 de Janeiro de 2026, 23:35  
**Status:** ✅ PROBLEMA IDENTIFICADO E DOCUMENTADO
