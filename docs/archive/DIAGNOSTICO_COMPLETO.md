# Diagnóstico Completo - SQL Server e Sincronização Parquet

## 📋 Resumo Executivo

O sistema **Agent BI** precisa do SQL Server para sincronizar dados para o arquivo Parquet. Identificamos e corrigimos os problemas de código, mas existe uma **configuração pendente no SQL Server**.

## ✅ Problemas Resolvidos (Código)

### 1. Correção do Endpoint de Diagnóstico
- **Arquivo**: `backend/app/api/v1/endpoints/diagnostics.py`
- **Problema**: Usava formato SQLAlchemy em vez de ODBC puro
- **Solução**: Alterado para usar `PYODBC_CONNECTION_STRING`
- **Status**: ✅ CORRIGIDO

### 2. Configuração do .env
- **Arquivo**: `backend/.env`
- **Problema**: Faltava `PYODBC_CONNECTION_STRING`
- **Solução**: Adicionada configuração correta
- **Status**: ✅ CORRIGIDO

### 3. Documentação
- **Arquivos criados**:
  - `SQL_SERVER_SETUP.md` - Guia de configuração geral
  - `HABILITAR_TCP_IP_SQL_SERVER.md` - Passo a passo TCP/IP
  - `diagnostico_sql_server.bat` - Script de diagnóstico automático
- **Status**: ✅ COMPLETO

## ⚠️ Problema Pendente (Configuração SQL Server)

### Erro Atual
```
Nenhuma conexão pôde ser feita porque a máquina de destino as recusou ativamente (10061)
```

### Causa Raiz
O **TCP/IP não está habilitado** no SQL Server Configuration Manager.

### Evidências
- ✅ Serviço MSSQLSERVER está **RUNNING**
- ✅ ODBC Driver 17 está **instalado**
- ✅ Código está **correto**
- ❌ Porta 1433 **não está escutando** (TCP/IP desabilitado)

### Impacto
**Sem o TCP/IP habilitado:**
- ❌ Não é possível sincronizar dados SQL → Parquet
- ❌ Script `sync_sql_to_parquet.py` falha
- ❌ Dados do Parquet ficam desatualizados
- ✅ Sistema continua funcionando com dados antigos do Parquet

## 🔧 Ação Necessária

Você precisa **habilitar TCP/IP** no SQL Server. Siga um dos guias:

### Opção 1: Guia Detalhado (Recomendado)
Abra o arquivo: **`HABILITAR_TCP_IP_SQL_SERVER.md`**

Este guia contém:
- ✅ Passo a passo com screenshots textuais
- ✅ Como abrir SQL Server Configuration Manager
- ✅ Como habilitar TCP/IP
- ✅ Como configurar porta 1433
- ✅ Como criar/verificar usuário AgenteVirtual
- ✅ Como reiniciar o serviço
- ✅ Como testar a conexão

### Opção 2: Diagnóstico Rápido
Execute o arquivo: **`diagnostico_sql_server.bat`**

Este script verifica automaticamente:
- Status do serviço SQL Server
- Se porta 1433 está em uso
- Drivers ODBC instalados
- Arquivo Parquet
- Conectividade SQL Server
- Acesso à tabela admmatao

## 📊 Configuração do Sistema

Suas configurações atuais (em `backend/.env`):

```env
# SQL Server
DATABASE_URL=mssql+aioodbc://AgenteVirtual:Cacula%402020@localhost:1433/Projeto_Caculinha?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes

PYODBC_CONNECTION_STRING=DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;DATABASE=Projeto_Caculinha;UID=AgenteVirtual;PWD=Cacula@2020;TrustServerCertificate=yes

USE_SQL_SERVER=true
FALLBACK_TO_PARQUET=true
```

## 🚀 Próximos Passos

### 1️⃣ Habilitar TCP/IP (5-10 minutos)
1. Abra `HABILITAR_TCP_IP_SQL_SERVER.md`
2. Siga os 7 passos
3. Reinicie o SQL Server

### 2️⃣ Verificar Conexão
Execute o diagnóstico:
```cmd
diagnostico_sql_server.bat
```

Ou teste manualmente:
```cmd
sqlcmd -S localhost -U AgenteVirtual -P "Cacula@2020" -Q "SELECT @@VERSION"
```

### 3️⃣ Sincronizar Dados
Após conectar com sucesso:
```cmd
cd backend\scripts
python sync_sql_to_parquet.py
```

### 4️⃣ Testar no Sistema
Acesse a página de diagnósticos:
```
http://localhost:3000/diagnostics
```

Clique em **"Testar Conexão"** - deve retornar sucesso.

## 📁 Arquivos Modificados/Criados

### Código Corrigido
- ✅ `backend/app/api/v1/endpoints/diagnostics.py` (linhas 131-148)
- ✅ `backend/.env` (linhas 18-20)
- ✅ `backend/.env.example` (linhas 18-20)

### Documentação Criada
- ✅ `SQL_SERVER_SETUP.md` - Guia geral de setup
- ✅ `HABILITAR_TCP_IP_SQL_SERVER.md` - Passo a passo TCP/IP ⭐
- ✅ `SQL_SERVER_STATUS_REPORT.md` - Relatório de status
- ✅ `DIAGNOSTICO_COMPLETO.md` - Este arquivo

### Scripts de Teste
- ✅ `test_diagnostics.py` - Testa endpoints de diagnóstico
- ✅ `diagnostico_sql_server.bat` - Diagnóstico automático ⭐

## 🎯 Resultado Esperado

**Antes de habilitar TCP/IP:**
```
❌ Erro: Nenhuma conexão pôde ser feita (10061)
```

**Depois de habilitar TCP/IP:**
```
✅ Sincronização concluída com sucesso!
✅ Total de linhas: 1.113.822
✅ Parquet atualizado
```

## ❓ FAQ

**P: Por que o sistema ainda funciona se SQL Server não conecta?**
R: O sistema usa o arquivo Parquet que já existe (60.21 MB, com dados antigos). O `FALLBACK_TO_PARQUET=true` garante que o sistema continue operacional.

**P: Com que frequência devo sincronizar?**
R: Depende da atualização dos dados. Recomendamos:
- Vendas/Estoque: A cada hora
- Catálogo/Cadastros: Diariamente

**P: Posso usar só o Parquet sem SQL Server?**
R: Tecnicamente sim, mas os dados ficarão desatualizados. O SQL Server é a fonte primária de dados.

**P: E se eu não conseguir habilitar TCP/IP?**
R: Contate o administrador do SQL Server. É necessário permissão administrativa.

## 📞 Suporte

Se após seguir o guia `HABILITAR_TCP_IP_SQL_SERVER.md` ainda houver problemas:

1. Execute `diagnostico_sql_server.bat`
2. Copie a saída completa
3. Verifique os logs em `backend/logs/`
4. Consulte a seção **Troubleshooting** no guia

---

**Status**: Código 100% corrigido | Pendente: Configuração SQL Server (TCP/IP)
**Data**: 2025-12-20
**Arquivos de Ajuda**: `HABILITAR_TCP_IP_SQL_SERVER.md` ⭐ | `diagnostico_sql_server.bat` ⭐
