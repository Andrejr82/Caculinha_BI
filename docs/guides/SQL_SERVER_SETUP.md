# Configuração do SQL Server - Agent Solution BI

## Problema Identificado

O erro `Nome da fonte de dados não encontrado e nenhum driver padrão especificado` ocorre quando a connection string ODBC não está configurada corretamente.

## Solução

### 1. Verificar Driver ODBC Instalado

Execute no PowerShell ou CMD:

```powershell
# Listar drivers ODBC instalados
odbcad32.exe

# Ou verificar via PowerShell
Get-OdbcDriver -Name "*SQL Server*"
```

**Drivers suportados:**
- `ODBC Driver 17 for SQL Server` (Recomendado)
- `ODBC Driver 18 for SQL Server`
- `SQL Server Native Client 11.0`

### 2. Instalar Driver ODBC (se necessário)

Se nenhum driver for encontrado, baixe e instale:

**ODBC Driver 17:**
https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

**ODBC Driver 18:**
https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

### 3. Configurar `.env` Corretamente

Edite `backend/.env` e adicione/atualize:

```env
# SQL Server habilitado
USE_SQL_SERVER=true

# Connection string para SQLAlchemy (DATABASE_URL)
DATABASE_URL=mssql+aioodbc://sa:SuaSenha@localhost/agentbi?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes

# Connection string ODBC pura (PYODBC_CONNECTION_STRING)
PYODBC_CONNECTION_STRING=DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=agentbi;UID=sa;PWD=SuaSenha;TrustServerCertificate=yes
```

#### Formato da PYODBC_CONNECTION_STRING:

```
DRIVER={DRIVER_NAME};SERVER=hostname;DATABASE=dbname;UID=username;PWD=password;TrustServerCertificate=yes
```

**Parâmetros:**
- `DRIVER`: Nome exato do driver ODBC (use `{...}` para nomes com espaços)
- `SERVER`: Hostname ou IP do SQL Server
  - Localhost: `localhost` ou `127.0.0.1`
  - Instância nomeada: `localhost\SQLEXPRESS`
  - Porta customizada: `localhost,1433`
- `DATABASE`: Nome do banco de dados
- `UID`: Username (ex: `sa`, `admin`, `user@domain` para Windows Auth)
- `PWD`: Password
- `TrustServerCertificate=yes`: Aceitar certificados auto-assinados

#### Exemplo com Windows Authentication:

```env
PYODBC_CONNECTION_STRING=DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\SQLEXPRESS;DATABASE=agentbi;Trusted_Connection=yes;TrustServerCertificate=yes
```

#### Exemplo com SQL Server Express:

```env
PYODBC_CONNECTION_STRING=DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\SQLEXPRESS;DATABASE=agentbi;UID=sa;PWD=MinhaSenh@123;TrustServerCertificate=yes
```

### 4. Reiniciar o Backend

Após configurar o `.env`:

```bash
# Parar o backend
taskkill /F /IM python.exe

# Reiniciar
cd backend
.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 5. Testar Conexão

Acesse: http://localhost:3000/diagnostics

Clique em **"Testar Conexão"** para validar.

## Modo Híbrido (Recomendado)

Se você **não precisa** do SQL Server, use apenas Parquet:

```env
USE_SQL_SERVER=false
FALLBACK_TO_PARQUET=true
```

O sistema funcionará perfeitamente com Parquet (mais rápido e sem dependências de SQL Server).

## Troubleshooting

### Erro: "Login failed for user 'sa'"
- Verifique se a senha está correta
- Verifique se a autenticação SQL está habilitada no SQL Server

### Erro: "Cannot open database"
- Verifique se o database existe
- Crie o database: `CREATE DATABASE agentbi;`

### Erro: "Named Pipes Provider"
- Verifique se o SQL Server está rodando
- Habilite TCP/IP no SQL Server Configuration Manager

### Verificar se SQL Server está rodando:

```powershell
Get-Service -Name "*SQL*"
```

Ou:

```cmd
services.msc
```

Procure por "SQL Server (MSSQLSERVER)" ou "SQL Server (SQLEXPRESS)" e verifique se está **Running**.

## Alternativas

Se você não tem SQL Server instalado e não quer instalar:

1. **Use somente Parquet** (modo atual do sistema):
   ```env
   USE_SQL_SERVER=false
   ```

2. **Use Supabase** (PostgreSQL cloud):
   ```env
   USE_SUPABASE_AUTH=true
   SUPABASE_URL=https://xxx.supabase.co
   SUPABASE_ANON_KEY=xxx
   ```

3. **Instale SQL Server Express** (gratuito):
   - Download: https://www.microsoft.com/en-us/sql-server/sql-server-downloads
   - Escolha "Express Edition"
