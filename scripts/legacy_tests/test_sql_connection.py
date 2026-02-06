#!/usr/bin/env python3
"""
Teste abrangente de conexão SQL Server
Usa as credenciais do arquivo .env para testar diferentes cenários
"""
import os
import sys
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Carregar variáveis de ambiente
from dotenv import load_dotenv
load_dotenv(backend_path / ".env")

print("=" * 80)
print("  TESTE DE CONEXÃO SQL SERVER - Agent BI")
print("=" * 80)
print()

# Extrair credenciais do .env
DATABASE_URL = os.getenv("DATABASE_URL")
PYODBC_CONNECTION_STRING = os.getenv("PYODBC_CONNECTION_STRING")
USE_SQL_SERVER = os.getenv("USE_SQL_SERVER", "false").lower() == "true"

print("[CONFIG] Configuracoes detectadas:")
print(f"   USE_SQL_SERVER: {USE_SQL_SERVER}")
print(f"   DATABASE_URL: {DATABASE_URL[:50]}..." if DATABASE_URL else "   DATABASE_URL: Nao configurado")
print(f"   PYODBC_CONNECTION_STRING: {PYODBC_CONNECTION_STRING[:50]}..." if PYODBC_CONNECTION_STRING else "   PYODBC_CONNECTION_STRING: Nao configurado")
print()

# Parsear credenciais da PYODBC_CONNECTION_STRING
if PYODBC_CONNECTION_STRING:
    import re
    server_match = re.search(r'SERVER=([^;]+)', PYODBC_CONNECTION_STRING)
    database_match = re.search(r'DATABASE=([^;]+)', PYODBC_CONNECTION_STRING)
    uid_match = re.search(r'UID=([^;]+)', PYODBC_CONNECTION_STRING)
    pwd_match = re.search(r'PWD=([^;]+)', PYODBC_CONNECTION_STRING)
    driver_match = re.search(r'DRIVER=\{([^}]+)\}', PYODBC_CONNECTION_STRING)

    SERVER = server_match.group(1) if server_match else "localhost"
    DATABASE = database_match.group(1) if database_match else "master"
    USERNAME = uid_match.group(1) if uid_match else "sa"
    PASSWORD = pwd_match.group(1) if pwd_match else ""
    DRIVER = driver_match.group(1) if driver_match else "ODBC Driver 17 for SQL Server"

    print("[CREDENCIAIS] Extraidas do .env:")
    print(f"   Servidor: {SERVER}")
    print(f"   Banco: {DATABASE}")
    print(f"   Usuario: {USERNAME}")
    print(f"   Senha: {'*' * len(PASSWORD)}")
    print(f"   Driver: {DRIVER}")
    print()

# Teste 1: Verificar drivers ODBC disponíveis
print("=" * 80)
print("TESTE 1: Drivers ODBC Instalados")
print("=" * 80)
try:
    import pyodbc
    drivers = pyodbc.drivers()
    print(f" pyodbc instalado (versão {pyodbc.version})")
    print(f" Drivers disponíveis ({len(drivers)}):")
    for driver in drivers:
        if 'SQL Server' in driver:
            print(f"    {driver}")

    if DRIVER in drivers:
        print(f"\n Driver configurado '{DRIVER}' está disponível!")
    else:
        print(f"\n  Driver configurado '{DRIVER}' NÃO encontrado!")
        print("   Drivers SQL Server disponíveis:")
        for d in drivers:
            if 'SQL Server' in d:
                print(f"      - {d}")
except ImportError as e:
    print(f" pyodbc não está instalado: {e}")
    sys.exit(1)
print()

# Teste 2: Tentar conexão com PYODBC_CONNECTION_STRING
print("=" * 80)
print("TESTE 2: Conexão usando PYODBC_CONNECTION_STRING")
print("=" * 80)
if PYODBC_CONNECTION_STRING:
    try:
        print(f" Tentando conectar...")
        print(f"   String: {PYODBC_CONNECTION_STRING[:80]}...")
        import pyodbc
        conn = pyodbc.connect(PYODBC_CONNECTION_STRING, timeout=5)
        print(" CONEXÃO ESTABELECIDA COM SUCESSO!")

        # Testar query
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print(f"\n Versão do SQL Server:")
        print(f"   {version.split(chr(10))[0]}")

        cursor.execute("SELECT DB_NAME()")
        db_name = cursor.fetchone()[0]
        print(f"\n Banco conectado: {db_name}")

        cursor.close()
        conn.close()

    except pyodbc.Error as e:
        print(f" ERRO DE CONEXÃO:")
        error_msg = str(e)
        print(f"   {error_msg}")

        # Diagnosticar erro
        if "10061" in error_msg or "recusou" in error_msg.lower():
            print("\n DIAGNÓSTICO:")
            print("     TCP/IP não está habilitado ou SQL Server não está escutando na porta")
            print("    Solução: Habilite TCP/IP no SQL Server Configuration Manager")
            print("    Veja: HABILITAR_TCP_IP_SQL_SERVER.md")
        elif "18456" in error_msg or "Login failed" in error_msg:
            print("\n DIAGNÓSTICO:")
            print("     Usuário ou senha incorretos")
            print("    Solução: Verifique as credenciais ou crie o usuário")
        elif "4060" in error_msg or "Cannot open database" in error_msg:
            print("\n DIAGNÓSTICO:")
            print("     Banco de dados não existe")
            print(f"    Solução: Crie o banco '{DATABASE}' ou conecte a outro banco")
        elif "IM002" in error_msg or "Data source" in error_msg:
            print("\n DIAGNÓSTICO:")
            print("     Driver ODBC não encontrado")
            print(f"    Solução: Instale o driver '{DRIVER}'")
else:
    print("  PYODBC_CONNECTION_STRING não configurado no .env")
print()

# Teste 3: Tentar com Windows Authentication
print("=" * 80)
print("TESTE 3: Conexão com Windows Authentication (Trusted_Connection)")
print("=" * 80)
try:
    windows_conn_string = f"DRIVER={{{DRIVER}}};SERVER={SERVER};DATABASE=master;Trusted_Connection=yes;TrustServerCertificate=yes"
    print(f" Tentando conectar com Windows Auth...")
    conn = pyodbc.connect(windows_conn_string, timeout=5)
    print(" CONEXÃO COM WINDOWS AUTH ESTABELECIDA!")

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sys.databases ORDER BY name")
    databases = [row[0] for row in cursor.fetchall()]
    print(f"\n Bancos de dados disponíveis ({len(databases)}):")
    for db in databases[:10]:
        marker = "" if db == DATABASE else "  "
        print(f"   {marker} {db}")
    if len(databases) > 10:
        print(f"   ... e mais {len(databases) - 10} bancos")

    # Verificar se o banco alvo existe
    if DATABASE in databases:
        print(f"\n Banco '{DATABASE}' EXISTE no servidor!")

        # Tentar conectar no banco específico
        cursor.execute(f"USE [{DATABASE}]")
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\n Tabelas no banco '{DATABASE}' ({len(tables)}):")
        for table in tables[:15]:
            print(f"   - {table}")
        if len(tables) > 15:
            print(f"   ... e mais {len(tables) - 15} tabelas")

        # Verificar se existe admmatao
        if 'admmatao' in [t.lower() for t in tables]:
            print(f"\n Tabela 'admmatao' ENCONTRADA!")
            cursor.execute("SELECT COUNT(*) FROM admmatao")
            count = cursor.fetchone()[0]
            print(f"    Total de registros: {count:,}")
    else:
        print(f"\n Banco '{DATABASE}' NÃO EXISTE no servidor!")
        print("    Solução: Crie o banco ou atualize o .env para usar outro banco")

    cursor.close()
    conn.close()

except pyodbc.Error as e:
    print(f" Erro com Windows Auth: {str(e)[:200]}")
print()

# Teste 4: Verificar se usuário SQL existe
print("=" * 80)
print("TESTE 4: Verificar se usuário SQL existe")
print("=" * 80)
try:
    windows_conn_string = f"DRIVER={{{DRIVER}}};SERVER={SERVER};DATABASE=master;Trusted_Connection=yes;TrustServerCertificate=yes"
    conn = pyodbc.connect(windows_conn_string, timeout=5)
    cursor = conn.cursor()

    cursor.execute(f"SELECT name, create_date, is_disabled FROM sys.sql_logins WHERE name = '{USERNAME}'")
    user = cursor.fetchone()

    if user:
        print(f" Usuário SQL '{USERNAME}' EXISTE!")
        print(f"   Criado em: {user[1]}")
        print(f"   Desabilitado: {'Sim' if user[2] else 'Não'}")

        # Verificar permissões no banco
        if DATABASE in [row[0] for row in cursor.execute("SELECT name FROM sys.databases").fetchall()]:
            cursor.execute(f"USE [{DATABASE}]")
            cursor.execute(f"SELECT name FROM sys.database_principals WHERE name = '{USERNAME}'")
            db_user = cursor.fetchone()
            if db_user:
                print(f" Usuário '{USERNAME}' tem acesso ao banco '{DATABASE}'")
            else:
                print(f"  Usuário '{USERNAME}' NÃO tem acesso ao banco '{DATABASE}'")
                print(f"    Solução: Execute 'CREATE USER [{USERNAME}] FOR LOGIN [{USERNAME}]' no banco")
    else:
        print(f" Usuário SQL '{USERNAME}' NÃO EXISTE!")
        print(f"\n Solução: Crie o usuário com:")
        print(f"   CREATE LOGIN [{USERNAME}] WITH PASSWORD = '{PASSWORD}';")
        print(f"   USE [{DATABASE}];")
        print(f"   CREATE USER [{USERNAME}] FOR LOGIN [{USERNAME}];")
        print(f"   ALTER ROLE db_datareader ADD MEMBER [{USERNAME}];")

    cursor.close()
    conn.close()

except pyodbc.Error as e:
    print(f"  Não foi possível verificar (Windows Auth necessária): {str(e)[:150]}")
print()

# Teste 5: Verificar porta 1433
print("=" * 80)
print("TESTE 5: Verificar porta TCP 1433")
print("=" * 80)
import socket

def check_port(host, port, timeout=3):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

hosts_to_test = [
    ("localhost", 1433),
    ("127.0.0.1", 1433),
]

for host, port in hosts_to_test:
    if check_port(host, port):
        print(f" {host}:{port} - PORTA ABERTA E ACESSÍVEL")
    else:
        print(f" {host}:{port} - PORTA FECHADA OU INACESSÍVEL")
        print(f"    TCP/IP pode estar desabilitado no SQL Server")
print()

# Resumo final
print("=" * 80)
print("RESUMO E RECOMENDAÇÕES")
print("=" * 80)
print()
print(" Para o sistema funcionar corretamente, você precisa:")
print()
print("1.  Driver ODBC instalado")
print(f"2. {'' if check_port('localhost', 1433) else ''} TCP/IP habilitado na porta 1433")
print("3.  Banco de dados 'Projeto_Caculinha' criado")
print(f"4.  Usuário '{USERNAME}' criado com senha correta")
print("5.  Permissões concedidas no banco")
print()
print(" Próximos passos:")
print("   - Se porta 1433 fechada: Veja HABILITAR_TCP_IP_SQL_SERVER.md")
print("   - Após resolver: Execute 'python backend/scripts/sync_sql_to_parquet.py'")
print()
print("=" * 80)
