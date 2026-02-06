"""
Diagnostico Avancado de Conexao SQL Server
Identifica e resolve problemas comuns de conectividade
"""
import os
import sys
import socket
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Carrega variaveis de ambiente
backend_dir = Path(__file__).parent
load_dotenv(backend_dir / ".env")

print("="*80)
print("DIAGNOSTICO AVANCADO - SQL SERVER")
print("="*80)
print()

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print("="*80)

def print_check(name, status, details=""):
    symbol = "[OK]" if status else "[ERRO]"
    print(f"{symbol} {name}")
    if details:
        print(f"    {details}")

# 1. VERIFICAR CONFIGURACAO DO .ENV
print_section("1. CONFIGURACAO DO .ENV")

database_url = os.getenv("DATABASE_URL", "")
pyodbc_string = os.getenv("PYODBC_CONNECTION_STRING", "")

print(f"DATABASE_URL: {database_url}")
print(f"PYODBC_CONNECTION_STRING: {pyodbc_string}")
print()

# Extrair informacoes da connection string
config = {}
server_full = "localhost"
host = "localhost"
port = 1433

if "SERVER=" in pyodbc_string:
    parts = pyodbc_string.split(";")
    for part in parts:
        if "=" in part:
            key, value = part.split("=", 1)
            config[key.strip()] = value.strip()
    
    server = config.get("SERVER", "")
    database = config.get("DATABASE", "")
    user = config.get("UID", "")
    driver = config.get("DRIVER", "")
    
    print(f"Servidor extraido: {server}")
    print(f"Database: {database}")
    print(f"Usuario: {user}")
    print(f"Driver: {driver}")
    print()
    
    server_full = server

# 2. TESTAR RESOLUCAO DNS / CONECTIVIDADE DE REDE
print_section("2. TESTE DE CONECTIVIDADE DE REDE")

# Extrair host e porta
if config and "SERVER" in config:
    server_full = config.get("SERVER", "localhost")
    
    # Separar host e porta se houver
    if "," in server_full:
        host, port_str = server_full.split(",")
        port = int(port_str)
    elif "\\" in server_full:
        # Instancia nomeada
        host = server_full.split("\\")[0]
        port = 1433  # Porta padrao
        print(f"[INFO] Instancia nomeada detectada: {server_full}")
        print(f"       SQL Server Browser deve estar rodando na porta UDP 1434")
    else:
        host = server_full
        port = 1433
    
    print(f"Host: {host}")
    print(f"Porta: {port}")
    print()
    
    # Teste 1: Resolver DNS
    try:
        ip = socket.gethostbyname(host)
        print_check(f"Resolucao DNS de '{host}'", True, f"IP: {ip}")
    except socket.gaierror as e:
        print_check(f"Resolucao DNS de '{host}'", False, f"Erro: {e}")
        print("\n[SOLUCAO 1] O hostname nao pode ser resolvido:")
        print("  - Se for localhost, tente usar '127.0.0.1' ou '(local)'")
        print("  - Se for um servidor remoto, verifique o nome do servidor")
        print("  - Tente usar o IP diretamente ao inves do hostname")
    
    # Teste 2: Testar conectividade TCP
    print()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host if host != "localhost" else "127.0.0.1", port))
        sock.close()
        
        if result == 0:
            print_check(f"Conexao TCP na porta {port}", True, "Porta acessivel")
        else:
            print_check(f"Conexao TCP na porta {port}", False, f"Codigo de erro: {result}")
            print("\n[SOLUCAO 2] A porta TCP nao esta acessivel:")
            print("  - Verifique se o SQL Server esta rodando")
            print("  - Verifique se o TCP/IP esta habilitado no SQL Server Configuration Manager")
            print("  - Verifique o firewall do Windows")
            print("  - Se usar instancia nomeada, verifique se SQL Server Browser esta rodando")
    except Exception as e:
        print_check(f"Conexao TCP na porta {port}", False, str(e))
else:
    print("[AVISO] PYODBC_CONNECTION_STRING nao configurado ou invalido")

# 3. VERIFICAR DRIVERS ODBC INSTALADOS
print_section("3. DRIVERS ODBC INSTALADOS")

try:
    import pyodbc
    drivers = pyodbc.drivers()
    print(f"Drivers ODBC disponiveis ({len(drivers)}):")
    for driver in drivers:
        print(f"  - {driver}")
    
    # Verificar se o driver especificado existe
    if driver in config:
        required_driver = config["DRIVER"].replace("{", "").replace("}", "")
        if required_driver in drivers:
            print_check(f"Driver '{required_driver}'", True, "Instalado")
        else:
            print_check(f"Driver '{required_driver}'", False, "NAO encontrado")
            print("\n[SOLUCAO 3] Driver ODBC nao encontrado:")
            print("  - Instale o ODBC Driver 17 ou 18 para SQL Server")
            print("  - Download: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server")
            print("  - Ou use um driver disponivel na lista acima")
except ImportError:
    print_check("pyodbc", False, "Modulo nao instalado")
    print("\n[SOLUCAO] Instale: pip install pyodbc")

# 4. TESTAR SERVICOS DO SQL SERVER
print_section("4. SERVICOS DO SQL SERVER (Windows)")

try:
    # Listar servicos do SQL Server
    result = subprocess.run(
        ['sc', 'query', 'type=', 'service', 'state=', 'all'],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    services = result.stdout
    sql_services = [line for line in services.split('\n') if 'SQL' in line.upper()]
    
    if sql_services:
        print("Servicos SQL Server encontrados:")
        for svc in sql_services[:10]:
            if svc.strip():
                print(f"  {svc.strip()}")
    else:
        print("[AVISO] Nenhum servico SQL Server encontrado")
        print("        SQL Server pode nao estar instalado nesta maquina")
        
except Exception as e:
    print(f"[INFO] Nao foi possivel listar servicos: {e}")

# 5. SUGESTOES DE CONNECTION STRING
print_section("5. SUGESTOES DE CONNECTION STRING")

print("Tente estas alternativas no seu .env:\n")

print("# Opcao 1: SQL Server local (instancia padrao)")
print('DATABASE_URL=mssql+aioodbc://sa:SuaSenha@127.0.0.1/agentbi?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes')
print('PYODBC_CONNECTION_STRING=DRIVER={ODBC Driver 17 for SQL Server};SERVER=127.0.0.1;DATABASE=agentbi;UID=sa;PWD=SuaSenha;TrustServerCertificate=yes')
print()

print("# Opcao 2: SQL Server local com (local)")
print('DATABASE_URL=mssql+aioodbc://sa:SuaSenha@(local)/agentbi?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes')
print('PYODBC_CONNECTION_STRING=DRIVER={ODBC Driver 17 for SQL Server};SERVER=(local);DATABASE=agentbi;UID=sa;PWD=SuaSenha;TrustServerCertificate=yes')
print()

print("# Opcao 3: SQL Server com instancia nomeada")
print('DATABASE_URL=mssql+aioodbc://sa:SuaSenha@localhost\\SQLEXPRESS/agentbi?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes')
print('PYODBC_CONNECTION_STRING=DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=agentbi;UID=sa;PWD=SuaSenha;TrustServerCertificate=yes')
print()

print("# Opcao 4: Autenticacao Windows (Trusted Connection)")
print('DATABASE_URL=mssql+aioodbc://@localhost/agentbi?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes&Trusted_Connection=yes')
print('PYODBC_CONNECTION_STRING=DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=agentbi;Trusted_Connection=yes;TrustServerCertificate=yes')
print()

print("# Opcao 5: ODBC Driver 18 (mais recente)")
print('DATABASE_URL=mssql+aioodbc://sa:SuaSenha@localhost/agentbi?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes&Encrypt=no')
print('PYODBC_CONNECTION_STRING=DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost;DATABASE=agentbi;UID=sa;PWD=SuaSenha;TrustServerCertificate=yes;Encrypt=no')
print()

# 6. CHECKLIST DE SOLUCOES
print_section("6. CHECKLIST DE SOLUCOES")

print("""
[ ] 1. SQL Server esta instalado e rodando?
      - Verifique no SQL Server Configuration Manager
      - Ou execute: sc query MSSQLSERVER

[ ] 2. TCP/IP esta habilitado?
      - Abra SQL Server Configuration Manager
      - SQL Server Network Configuration > Protocols for [INSTANCE]
      - TCP/IP deve estar "Enabled"

[ ] 3. SQL Server Browser esta rodando? (se usar instancia nomeada)
      - Execute: sc query SQLBrowser
      - Inicie se necessario: net start SQLBrowser

[ ] 4. Firewall permite conexoes?
      - Porta 1433 (TCP) para instancia padrao
      - Porta 1434 (UDP) para SQL Server Browser
      - Execute como admin: netsh advfirewall firewall add rule name="SQL Server" dir=in action=allow protocol=TCP localport=1433

[ ] 5. Autenticacao SQL Server esta habilitada?
      - SQL Server deve estar em modo "Mixed Mode"
      - Verifique nas propriedades do servidor no SSMS

[ ] 6. Usuario 'sa' esta habilitado e senha correta?
      - Ou use autenticacao Windows (Trusted_Connection=yes)

[ ] 7. Database existe?
      - Conecte via SSMS e verifique se o database 'agentbi' existe
      - Ou crie: CREATE DATABASE agentbi

[ ] 8. Considere usar apenas Parquet/DuckDB
      - Se SQL Server nao e essencial, desabilite:
      - USE_SQL_SERVER=false
      - FALLBACK_TO_PARQUET=true
""")

print_section("7. TESTE RAPIDO COM SQLCMD")

print("""
Execute este comando no terminal para testar a conexao diretamente:

sqlcmd -S localhost -U sa -P SuaSenha -Q "SELECT @@VERSION"

Se funcionar, o problema esta na connection string Python.
Se nao funcionar, o problema esta no SQL Server ou rede.
""")

print("\n" + "="*80)
print("FIM DO DIAGNOSTICO")
print("="*80)
