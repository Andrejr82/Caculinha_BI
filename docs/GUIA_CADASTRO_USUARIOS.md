# Guia de Cadastro de Usuários com Segmentos Restritos

**Data:** 2026-01-07
**Versão:** 1.0

---

## 📋 Visão Geral

O sistema permite criar usuários com acesso restrito a segmentos específicos de negócio (TECIDOS, ARMARINHO, PAPELARIA, etc.). Cada usuário verá **apenas os dados dos segmentos** para os quais foi autorizado.

## 🔐 Níveis de Acesso

### 1. Admin (Acesso Total)
- **Role:** `admin`
- **Segmentos:** Automático `["*"]` (todos os segmentos)
- **Páginas:** Acesso total a todas as funcionalidades

### 2. Usuário Comum (Acesso Restrito)
- **Role:** `user`
- **Segmentos:** Definidos manualmente durante o cadastro
- **Páginas:** Acesso limitado (sem /metrics, /reports, /admin, etc.)

---

## 🎯 Como Cadastrar Usuários via Interface

### Passo 1: Acessar Administração

1. Fazer login como `admin` / `admin`
2. No menu lateral, clicar em **"Administração"** (ícone de escudo)
3. Clicar na aba **"Usuários"**

### Passo 2: Criar Novo Usuário

1. Clicar no botão **"+ Novo Usuário"**
2. Preencher o formulário:
   - **Username:** Nome de usuário para login (ex: `analista_tecidos`)
   - **Email:** Email do usuário (ex: `analista.tecidos@cacaulinha.com`)
   - **Senha:** Senha de acesso (mín. 6 caracteres)
   - **Role:** Selecionar `user` (ou `admin` para acesso total)
   - **Segmentos Permitidos:** Marcar os segmentos autorizados

### Passo 3: Selecionar Segmentos

**Segmentos disponíveis no sistema:**
- `TECIDOS` - Tecidos e aviamentos
- `ARMARINHO` - Artigos de armarinho
- `PAPELARIA` - Papelaria e escolar
- `UTILIDADES` - Utilidades domésticas
- `BAZAR` - Bazar e decoração
- ... (outros segmentos do catálogo)

**Exemplos de configuração:**

| Perfil | Segmentos | Descrição |
|--------|-----------|-----------|
| Analista Tecidos | `[TECIDOS]` | Vê apenas produtos de tecidos |
| Analista Armarinho | `[ARMARINHO]` | Vê apenas produtos de armarinho |
| Gerente de Loja | `[TECIDOS, ARMARINHO, PAPELARIA]` | Vê múltiplos segmentos |
| Diretor Comercial | `["*"]` | Vê todos os segmentos (configurar role=admin) |

### Passo 4: Salvar e Testar

1. Clicar em **"Salvar"**
2. O usuário será criado no **Supabase Auth**
3. Fazer logout e testar o login com as novas credenciais

---

## 🧪 Exemplos de Usuários para Teste

### Exemplo 1: Analista de Tecidos

```
Username: analista_tecidos
Email: analista.tecidos@cacaulinha.com
Password: test123
Role: user
Segmentos: [TECIDOS]
```

**O que este usuário verá:**
- ✅ Produtos do segmento TECIDOS
- ✅ Vendas, estoque e análises APENAS de tecidos
- ❌ Produtos de outros segmentos (ARMARINHO, PAPELARIA, etc.)
- ❌ Páginas de administração

### Exemplo 2: Analista de Armarinho

```
Username: analista_armarinho
Email: analista.armarinho@cacaulinha.com
Password: test123
Role: user
Segmentos: [ARMARINHO]
```

**O que este usuário verá:**
- ✅ Produtos do segmento ARMARINHO
- ✅ Vendas, estoque e análises APENAS de armarinho
- ❌ Produtos de outros segmentos
- ❌ Páginas de administração

### Exemplo 3: Gerente Multi-Segmento

```
Username: gerente_loja
Email: gerente.loja@cacaulinha.com
Password: test123
Role: user
Segmentos: [TECIDOS, ARMARINHO, PAPELARIA]
```

**O que este usuário verá:**
- ✅ Produtos dos 3 segmentos selecionados
- ✅ Análises consolidadas dos 3 segmentos
- ❌ Outros segmentos (BAZAR, UTILIDADES, etc.)
- ❌ Páginas de administração

---

## 🔍 Como Funciona a Restrição

### Backend (API)

Todas as queries de dados passam pelo `DataScopeService`:

```python
# backend/app/core/data_scope_service.py:72-93
if user.role == "admin" or "*" in user.segments_list:
    # Admin: Sem filtro de segmento
    pass
else:
    # Usuário comum: Filtra por segmentos permitidos
    segments_str = ", ".join(["'{}'".format(s) for s in allowed_segments])
    rel = rel.filter(f"NOMESEGMENTO IN ({segments_str})")
```

### Frontend (Interface)

As rotas protegidas verificam a role do usuário:

```typescript
// frontend-solid/src/index.tsx:54-58
when={
  auth.user()?.role === 'admin' ||           // Admin sempre acessa
  auth.user()?.role === props.requiredRole || // Role corresponde
  auth.user()?.allowed_segments?.includes('*') // Ou tem acesso total
}
```

### Token JWT

O token de autenticação contém os segmentos:

```json
{
  "sub": "user-id",
  "username": "analista_tecidos",
  "role": "user",
  "allowed_segments": ["TECIDOS"],  ← Segmentos autorizados
  "exp": 1767835144
}
```

---

## 📊 Validação da Restrição

### Teste 1: Query de Dados

```bash
# Login como usuário restrito
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"analista_tecidos","password":"test123"}'

# Usar o token retornado para buscar produtos
curl -X GET http://localhost:8000/api/v1/analytics/filter-options \
  -H "Authorization: Bearer <TOKEN>"
```

**Resultado esperado:**
- `segmentos: ["TECIDOS"]` (somente o segmento autorizado)

### Teste 2: Interface Gráfica

1. Fazer login como `analista_tecidos`
2. Ir para página **Analytics** ou **Dashboard**
3. Filtros de segmento mostrarão **apenas TECIDOS**
4. Gráficos e tabelas mostrarão **apenas dados de TECIDOS**

### Teste 3: Tentativa de Acesso Não Autorizado

1. Fazer login como `analista_tecidos`
2. Tentar acessar `/admin` ou `/metrics`
3. **Resultado:** Página "Acesso Negado - 403 Forbidden"

---

## ⚠️ Observações Importantes

### 1. Admin Sempre Tem Acesso Total

```python
# backend/app/core/auth_service.py:348-352
if role == "admin":
    allowed_segments = ["*"]  # Admin sempre tem acesso total
    security_logger.info(f"Admin user '{username}' granted full access")
```

**Não é possível criar admin com acesso restrito** - o sistema força `["*"]` automaticamente.

### 2. Segmentos São Case-Sensitive

- Correto: `TECIDOS`
- Errado: `tecidos` ou `Tecidos`

Os nomes dos segmentos devem corresponder **exatamente** aos valores na coluna `NOMESEGMENTO` do Parquet.

### 3. Usuário Sem Segmentos

Se criar um usuário com `allowed_segments: []` (vazio):
- ❌ Não verá **nenhum dado**
- ❌ Todas as queries retornarão vazio
- ⚠️ Sistema exibirá "Nenhum dado disponível"

---

## 🛠️ Troubleshooting

### Problema: Usuário vê dados de todos os segmentos

**Causa:** Token JWT antigo ou role=admin
**Solução:**
1. Fazer logout
2. Fazer login novamente (gera novo token)
3. Verificar role do usuário (não pode ser `admin`)

### Problema: Usuário não vê nenhum dado

**Causa:** `allowed_segments` vazio ou segmentos incorretos
**Solução:**
1. Verificar segmentos do usuário em `/admin` → Usuários
2. Editar usuário e selecionar segmentos corretos
3. Fazer logout/login

### Problema: Erro ao criar usuário

**Causa:** Supabase não configurado ou credenciais inválidas
**Solução:**
1. Verificar `.env`:
   ```bash
   USE_SUPABASE_AUTH=true
   SUPABASE_URL=https://nmamxbriulivinlqqbmf.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=<key>
   ```
2. Reiniciar backend

---

## 📚 Arquivos de Referência

### Backend
- **Auth Service:** `backend/app/core/auth_service.py:348-352` (Admin full access)
- **Data Scope:** `backend/app/core/data_scope_service.py:72-93` (Segment filter)
- **Supabase Service:** `backend/app/core/supabase_user_service.py:38-106` (User creation)

### Frontend
- **Route Guard:** `frontend-solid/src/index.tsx:54-58` (Role verification)
- **Auth Store:** `frontend-solid/src/store/auth.ts:73-75` (Admin check)
- **Admin Page:** `frontend-solid/src/pages/Admin.tsx` (User management UI)

---

**Última atualização:** 2026-01-07
**Status:** ✅ Totalmente implementado e testado
