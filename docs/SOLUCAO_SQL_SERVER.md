# Guia Completo de Solução - Problema de Conexão SQL Server

## 📋 Resumo do Problema

**Erro identificado:**
```
pyodbc.OperationalError: ('08001', '[08001] [Microsoft][ODBC Driver 17 for SQL Server]
Provedor TCP: Erro irrecuperável durante uma pesquisa em um banco de dados.
O servidor não foi encontrado ou não está acessível.
```

**Status atual dos bancos de dados:**
- ✅ **Supabase**: Funcionando perfeitamente
- ✅ **DuckDB**: Funcionando perfeitamente  
- ✅ **Arquivos Parquet**: Funcionando perfeitamente (1.113.822 registros em admmat.parquet)
- ❌ **SQL Server**: Falha de conexão

---

## 🎯 Soluções Práticas (em ordem de prioridade)

### SOLUÇÃO 1: Desabilitar SQL Server e usar apenas Parquet/DuckDB ⭐ RECOMENDADO

**Esta é a solução mais rápida e eficiente!**

Você já tem todos os dados funcionando perfeitamente em arquivos Parquet. O sistema está configurado para fallback automático.

**Passos:**

1. Edite o arquivo `backend/.env`:
   ```env
   USE_SQL_SERVER=false
   FALLBACK_TO_PARQUET=true
   ```

2. Reinicie o backend

**Vantagens:**
- ✅ Solução imediata
- ✅ Melhor performance (DuckDB é extremamente rápido)
- ✅ Sem dependência de servidor SQL
- ✅ Mais fácil de fazer deploy
- ✅ Seus dados já estão todos em Parquet

---

### SOLUÇÃO 2: Verificar se SQL Server está instalado e rodando

Se você realmente precisa do SQL Server, siga estes passos:

#### 2.1. Verificar se SQL Server está instalado

Execute no PowerShell como Administrador:

```powershell
# Listar serviços SQL Server
Get-Service | Where-Object {$_.Name -like "*SQL*"}
```

**Resultado esperado:**
```
Status   Name               DisplayName
------   ----               -----------
Running  MSSQLSERVER        SQL Server (MSSQLSERVER)
Running  SQLBrowser         SQL Server Browser
```

#### 2.2. Se SQL Server NÃO estiver instalado

**Opções:**

**A) Instalar SQL Server Express (Gratuito)**
- Download: https://www.microsoft.com/sql-server/sql-server-downloads
- Escolha: SQL Server 2022 Express
- Durante instalação: Habilite "Mixed Mode Authentication" e defina senha para 'sa'

**B) Usar SQL Server via Docker**
```powershell
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=SuaSenha@123" `
  -p 1433:1433 --name sqlserver `
  -d mcr.microsoft.com/mssql/server:2022-latest
```

#### 2.3. Se SQL Server estiver instalado mas parado

```powershell
# Iniciar SQL Server
net start MSSQLSERVER

# Iniciar SQL Server Browser (para instâncias nomeadas)
net start SQLBrowser
```

---

### SOLUÇÃO 3: Corrigir a Connection String

Baseado no erro, o problema pode estar na connection string. Teste estas alternativas:

#### 3.1. Identificar sua instância SQL Server

```powershell
# Listar instâncias SQL Server instaladas
Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server' | 
  Select-Object InstalledInstances
```

**Resultados possíveis:**
- `MSSQLSERVER` = Instância padrão → use `localhost` ou `127.0.0.1`
- `SQLEXPRESS` = Instância nomeada → use `localhost\SQLEXPRESS`

#### 3.2. Atualizar `.env` com a configuração correta

**Para instância padrão (MSSQLSERVER):**
```env
DATABASE_URL=mssql+aioodbc://sa:SuaSenha@127.0.0.1/agentbi?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes

PYODBC_CONNECTION_STRING=DRIVER={ODBC Driver 17 for SQL Server};SERVER=127.0.0.1;DATABASE=agentbi;UID=sa;PWD=SuaSenha;TrustServerCertificate=yes
```

**Para SQL Server Express:**
```env
DATABASE_URL=mssql+aioodbc://sa:SuaSenha@localhost\\SQLEXPRESS/agentbi?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes

PYODBC_CONNECTION_STRING=DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\SQLEXPRESS;DATABASE=agentbi;UID=sa;PWD=SuaSenha;TrustServerCertificate=yes
```

**Para autenticação Windows:**
```env
DATABASE_URL=mssql+aioodbc://@localhost/agentbi?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes&Trusted_Connection=yes

PYODBC_CONNECTION_STRING=DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=agentbi;Trusted_Connection=yes;TrustServerCertificate=yes
```

---

### SOLUÇÃO 4: Habilitar TCP/IP no SQL Server

1. Abra **SQL Server Configuration Manager**
   - Pressione `Win + R` → digite `SQLServerManager16.msc` (ou 15, 14 dependendo da versão)

2. Navegue até:
   - **SQL Server Network Configuration** → **Protocols for [SUA_INSTÂNCIA]**

3. Clique com botão direito em **TCP/IP** → **Enable**

4. Clique com botão direito em **TCP/IP** → **Properties**
   - Aba **IP Addresses**
   - Role até **IPAll**
   - **TCP Port**: `1433`
   - Clique **OK**

5. Reinicie o serviço SQL Server:
   ```powershell
   net stop MSSQLSERVER
   net start MSSQLSERVER
   ```

---

### SOLUÇÃO 5: Configurar Firewall

Execute no PowerShell como Administrador:

```powershell
# Permitir SQL Server (porta 1433)
New-NetFirewallRule -DisplayName "SQL Server" -Direction Inbound `
  -Protocol TCP -LocalPort 1433 -Action Allow

# Permitir SQL Browser (porta 1434 UDP) - para instâncias nomeadas
New-NetFirewallRule -DisplayName "SQL Browser" -Direction Inbound `
  -Protocol UDP -LocalPort 1434 -Action Allow
```

---

### SOLUÇÃO 6: Criar o Database se não existir

Se SQL Server estiver rodando mas o database 'agentbi' não existe:

```powershell
# Conectar via sqlcmd
sqlcmd -S localhost -U sa -P SuaSenha

# Criar database
CREATE DATABASE agentbi;
GO

# Verificar
SELECT name FROM sys.databases;
GO

# Sair
EXIT
```

---

## 🔍 Scripts de Diagnóstico Criados

Foram criados 3 scripts para ajudar no diagnóstico:

### 1. `test_db_connections.py`
Testa todas as conexões configuradas no .env

```bash
python test_db_connections.py
```

### 2. `test_db_connections_html.py`
Gera relatório HTML visual dos testes

```bash
python test_db_connections_html.py
```

### 3. `diagnose_sqlserver.py`
Diagnóstico completo de problemas SQL Server

```bash
python diagnose_sqlserver.py
```

### 4. `test_all_connections.py`
Testa automaticamente múltiplas connection strings

```bash
python test_all_connections.py
```

---

## 💡 Recomendação Final

**Como desenvolvedor sênior, minha recomendação é:**

### ⭐ Use a SOLUÇÃO 1 (Desabilitar SQL Server)

**Motivos:**

1. **Seus dados já estão em Parquet** - 1.113.822 registros funcionando perfeitamente
2. **DuckDB é mais rápido** que SQL Server para análises
3. **Sem complexidade de infraestrutura** - não precisa gerenciar servidor SQL
4. **Mais fácil de fazer deploy** - apenas arquivos
5. **Supabase já está funcionando** para autenticação
6. **Arquitetura híbrida já implementada** - o sistema foi projetado para isso

### Se realmente precisar de SQL Server:

Siga as soluções 2-6 nesta ordem:
1. Verificar se está instalado (Solução 2)
2. Corrigir connection string (Solução 3)
3. Habilitar TCP/IP (Solução 4)
4. Configurar firewall (Solução 5)
5. Criar database (Solução 6)

---

## 📞 Próximos Passos

**Escolha uma opção:**

**OPÇÃO A - Usar apenas Parquet/DuckDB (RECOMENDADO)**
```bash
# 1. Editar backend/.env
USE_SQL_SERVER=false
FALLBACK_TO_PARQUET=true

# 2. Reiniciar backend
# Pronto! Sistema funcionando
```

**OPÇÃO B - Resolver problema SQL Server**
```bash
# 1. Executar diagnóstico
python diagnose_sqlserver.py

# 2. Testar connection strings
python test_all_connections.py

# 3. Seguir soluções 2-6 conforme necessário
```

---

## 📊 Status Atual do Sistema

| Componente | Status | Registros | Observação |
|------------|--------|-----------|------------|
| Parquet Files | ✅ OK | 1.113.822 | admmat.parquet funcionando |
| DuckDB | ✅ OK | - | v1.4.3 operacional |
| Supabase | ✅ OK | - | Autenticação funcionando |
| SQL Server | ❌ ERRO | - | Conexão falhando |

**Conclusão:** O sistema pode funcionar perfeitamente SEM SQL Server!

---

## 🛠️ Comandos Úteis de Diagnóstico

```powershell
# Verificar se SQL Server está ouvindo na porta 1433
Test-NetConnection -ComputerName localhost -Port 1433

# Listar portas em uso
netstat -ano | findstr :1433

# Verificar serviços SQL
Get-Service | Where-Object {$_.Name -like "*SQL*"}

# Testar conexão com sqlcmd
sqlcmd -S localhost -U sa -P SuaSenha -Q "SELECT @@VERSION"

# Ver drivers ODBC instalados
python -c "import pyodbc; print('\n'.join(pyodbc.drivers()))"
```

---

**Criado em:** 2026-01-01  
**Versão:** 1.0  
**Autor:** Diagnóstico Automático SQL Server
