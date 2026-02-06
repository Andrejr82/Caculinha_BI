# Como Habilitar TCP/IP no SQL Server

## Problema Identificado

```
Erro: Nenhuma conexão pôde ser feita porque a máquina de destino as recusou ativamente (10061)
```

Isso significa que o **SQL Server está rodando**, mas **TCP/IP não está habilitado**.

## Solução Passo a Passo

### Passo 1: Abrir SQL Server Configuration Manager

1. Pressione `Windows + R`
2. Digite: `SQLServerManager15.msc` (SQL Server 2019)
   - **SQL Server 2022**: `SQLServerManager16.msc`
   - **SQL Server 2017**: `SQLServerManager14.msc`
   - **SQL Server 2016**: `SQLServerManager13.msc`
3. Clique em **OK**

**Alternativa:** Procure no menu Iniciar por "SQL Server Configuration Manager"

### Passo 2: Habilitar TCP/IP

1. No painel esquerdo, expanda **"SQL Server Network Configuration"**
2. Clique em **"Protocols for MSSQLSERVER"** (ou sua instância)
3. No painel direito, clique com botão direito em **"TCP/IP"**
4. Selecione **"Enable"** (Habilitar)

### Passo 3: Configurar a Porta 1433

1. Ainda com TCP/IP selecionado, clique com botão direito e escolha **"Properties"**
2. Vá para a aba **"IP Addresses"**
3. Role até a seção **"IPAll"** (no final)
4. Configure:
   - **TCP Dynamic Ports**: `<deixe vazio>`
   - **TCP Port**: `1433`
5. Clique em **OK**

### Passo 4: Habilitar SQL Server Authentication

1. Abra **SQL Server Management Studio (SSMS)**
2. Conecte-se ao servidor: `localhost` (usando Windows Authentication)
3. Clique com botão direito no servidor (raiz) > **Properties**
4. Vá para a página **"Security"**
5. Em **"Server authentication"**, selecione:
   - ✅ **"SQL Server and Windows Authentication mode"**
6. Clique em **OK**

### Passo 5: Criar/Verificar o Usuário AgenteVirtual

No SQL Server Management Studio, execute:

```sql
-- Verificar se usuário existe
SELECT name FROM sys.sql_logins WHERE name = 'AgenteVirtual';

-- Se não existir, criar:
CREATE LOGIN [AgenteVirtual] WITH PASSWORD = 'Cacula@2020';

-- Criar usuário no banco Projeto_Caculinha
USE [Projeto_Caculinha];
CREATE USER [AgenteVirtual] FOR LOGIN [AgenteVirtual];

-- Dar permissões de leitura
ALTER ROLE db_datareader ADD MEMBER [AgenteVirtual];
```

### Passo 6: Reiniciar o SQL Server

**Método 1: Pelo Configuration Manager**
1. No SQL Server Configuration Manager
2. Clique em **"SQL Server Services"** no painel esquerdo
3. Clique com botão direito em **"SQL Server (MSSQLSERVER)"**
4. Selecione **"Restart"**

**Método 2: Por Linha de Comando (como Administrador)**
```cmd
net stop MSSQLSERVER
net start MSSQLSERVER
```

### Passo 7: Testar a Conexão

Após reiniciar, execute o script de teste:

```bash
cd C:\Agente_BI\BI_Solution\backend\scripts
python sync_sql_to_parquet.py
```

Ou teste via Diagnostics Page:
```
http://localhost:3000/diagnostics
```

## Verificações Rápidas

### Verificar se TCP/IP está escutando na porta 1433:
```cmd
netstat -an | findstr ":1433"
```

**Saída esperada:**
```
TCP    0.0.0.0:1433           0.0.0.0:0              LISTENING
TCP    [::]:1433              [::]:0                 LISTENING
```

### Verificar se SQL Server está rodando:
```cmd
sc query MSSQLSERVER
```

**Saída esperada:** `ESTADO: 4 RUNNING`

### Testar conexão via sqlcmd:
```cmd
sqlcmd -S localhost -U AgenteVirtual -P "Cacula@2020" -Q "SELECT @@VERSION"
```

## Troubleshooting

### Erro: "Login failed for user 'AgenteVirtual'"
- Verifique se o usuário foi criado (Passo 5)
- Verifique se SQL Server Authentication está habilitado (Passo 4)
- Confirme que a senha está correta

### Erro: "Cannot open database 'Projeto_Caculinha'"
- Verifique se o banco existe:
  ```sql
  SELECT name FROM sys.databases;
  ```
- Se não existir, crie ou atualize o `.env` para usar outro banco

### TCP/IP ainda não funciona após reiniciar
- Verifique o Windows Firewall:
  ```cmd
  netsh advfirewall firewall add rule name="SQL Server" dir=in action=allow protocol=TCP localport=1433
  ```

## Configuração Atual do Sistema

Seu sistema está configurado com:
- **Servidor**: localhost,1433
- **Banco**: Projeto_Caculinha
- **Usuário**: AgenteVirtual
- **Senha**: Cacula@2020
- **Driver**: ODBC Driver 17 for SQL Server ✅ (já instalado)

## Próximos Passos Após Habilitar TCP/IP

1. Execute o script de sincronização:
   ```bash
   cd backend/scripts
   python sync_sql_to_parquet.py
   ```

2. Configure sincronização automática (opcional):
   - Crie um Agendador de Tarefas do Windows
   - Execute o script diariamente/por hora
   - Mantenha o Parquet sempre atualizado

---

**Importante**: Após seguir estes passos, o erro de conexão será resolvido e você poderá sincronizar os dados do SQL Server para o Parquet normalmente.
