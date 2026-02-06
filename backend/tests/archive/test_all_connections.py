"""
Testador Automatico de Connection Strings SQL Server
Testa multiplas configuracoes para encontrar a que funciona
"""
import asyncio
import pyodbc
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Lista de connection strings para testar
test_configs = [
    {
        "name": "Localhost com IP 127.0.0.1",
        "pyodbc": "DRIVER={ODBC Driver 17 for SQL Server};SERVER=127.0.0.1;DATABASE=agentbi;UID=AgenteVirtual;PWD=Cacula@2020;TrustServerCertificate=yes",
        "sqlalchemy": "mssql+aioodbc://AgenteVirtual:Cacula@2020@127.0.0.1/agentbi?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
    },
    {
        "name": "Localhost com (local)",
        "pyodbc": "DRIVER={ODBC Driver 17 for SQL Server};SERVER=(local);DATABASE=agentbi;UID=AgenteVirtual;PWD=Cacula@2020;TrustServerCertificate=yes",
        "sqlalchemy": "mssql+aioodbc://AgenteVirtual:Cacula@2020@(local)/agentbi?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
    },
    {
        "name": "Localhost padrao",
        "pyodbc": "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=agentbi;UID=AgenteVirtual;PWD=Cacula@2020;TrustServerCertificate=yes",
        "sqlalchemy": "mssql+aioodbc://AgenteVirtual:Cacula@2020@localhost/agentbi?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
    },
    {
        "name": "SQLEXPRESS (instancia nomeada)",
        "pyodbc": "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=agentbi;UID=AgenteVirtual;PWD=Cacula@2020;TrustServerCertificate=yes",
        "sqlalchemy": "mssql+aioodbc://AgenteVirtual:Cacula@2020@localhost\\SQLEXPRESS/agentbi?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
    },
    {
        "name": "Autenticacao Windows (Trusted)",
        "pyodbc": "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=agentbi;Trusted_Connection=yes;TrustServerCertificate=yes",
        "sqlalchemy": "mssql+aioodbc://@localhost/agentbi?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes&Trusted_Connection=yes"
    },
    {
        "name": "ODBC Driver 18 (mais recente)",
        "pyodbc": "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost;DATABASE=agentbi;UID=AgenteVirtual;PWD=Cacula@2020;TrustServerCertificate=yes;Encrypt=no",
        "sqlalchemy": "mssql+aioodbc://AgenteVirtual:Cacula@2020@localhost/agentbi?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes&Encrypt=no"
    },
    {
        "name": "Porta especifica 1433",
        "pyodbc": "DRIVER={ODBC Driver 17 for SQL Server};SERVER=127.0.0.1,1433;DATABASE=agentbi;UID=AgenteVirtual;PWD=Cacula@2020;TrustServerCertificate=yes",
        "sqlalchemy": "mssql+aioodbc://AgenteVirtual:Cacula@2020@127.0.0.1:1433/agentbi?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
    }
]

print("="*80)
print("TESTADOR AUTOMATICO DE CONNECTION STRINGS")
print("="*80)
print()

successful_configs = []
failed_configs = []

async def test_sqlalchemy_connection(config):
    """Testa conexao usando SQLAlchemy"""
    try:
        engine = create_async_engine(
            config["sqlalchemy"],
            echo=False,
            pool_pre_ping=True,
            connect_args={"timeout": 5}
        )
        
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT @@VERSION"))
            version = result.scalar()
            
            result = await conn.execute(text("SELECT DB_NAME()"))
            dbname = result.scalar()
            
        await engine.dispose()
        
        return True, f"Database: {dbname}, Versao: {version[:60]}..."
    except Exception as e:
        return False, str(e)[:100]

def test_pyodbc_connection(config):
    """Testa conexao usando pyodbc direto"""
    try:
        conn = pyodbc.connect(config["pyodbc"], timeout=5)
        cursor = conn.cursor()
        
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        
        cursor.execute("SELECT DB_NAME()")
        dbname = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return True, f"Database: {dbname}, Versao: {version[:60]}..."
    except Exception as e:
        return False, str(e)[:100]

async def run_tests():
    """Executa todos os testes"""
    for i, config in enumerate(test_configs, 1):
        print(f"\n[{i}/{len(test_configs)}] Testando: {config['name']}")
        print("-" * 80)
        
        # Teste 1: pyodbc direto
        print("  [1] Testando pyodbc direto...")
        success, message = test_pyodbc_connection(config)
        
        if success:
            print(f"      [OK] {message}")
            successful_configs.append({
                "config": config,
                "method": "pyodbc",
                "message": message
            })
        else:
            print(f"      [ERRO] {message}")
            
            # Teste 2: SQLAlchemy (apenas se pyodbc falhou)
            print("  [2] Testando SQLAlchemy...")
            success2, message2 = await test_sqlalchemy_connection(config)
            
            if success2:
                print(f"      [OK] {message2}")
                successful_configs.append({
                    "config": config,
                    "method": "sqlalchemy",
                    "message": message2
                })
            else:
                print(f"      [ERRO] {message2}")
                failed_configs.append({
                    "config": config,
                    "error": message2
                })
    
    # Resultados finais
    print("\n" + "="*80)
    print("RESULTADOS FINAIS")
    print("="*80)
    
    if successful_configs:
        print(f"\n[SUCESSO] {len(successful_configs)} configuracao(oes) funcionaram!\n")
        
        for i, result in enumerate(successful_configs, 1):
            print(f"{i}. {result['config']['name']} ({result['method']})")
            print(f"   {result['message']}")
            print(f"\n   Use no seu .env:")
            print(f"   DATABASE_URL={result['config']['sqlalchemy']}")
            print(f"   PYODBC_CONNECTION_STRING={result['config']['pyodbc']}")
            print()
    else:
        print("\n[ERRO] Nenhuma configuracao funcionou!")
        print("\nPossiveis causas:")
        print("  1. SQL Server nao esta instalado ou rodando")
        print("  2. Database 'agentbi' nao existe")
        print("  3. Usuario/senha incorretos")
        print("  4. TCP/IP nao esta habilitado")
        print("  5. Firewall bloqueando conexoes")
        print("\nSolucao alternativa:")
        print("  - Use apenas Parquet/DuckDB:")
        print("    USE_SQL_SERVER=false")
        print("    FALLBACK_TO_PARQUET=true")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    try:
        asyncio.run(run_tests())
    except KeyboardInterrupt:
        print("\n\nTeste interrompido pelo usuario")
