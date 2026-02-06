"""
Script de Teste de Conexoes de Banco de Dados
Testa todas as conexoes configuradas no arquivo .env
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

# Configura encoding UTF-8 para Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Adiciona o diretorio backend ao path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Carrega variaveis de ambiente
load_dotenv(backend_dir / ".env")

print("=" * 80)
print("TESTE DE CONEXOES DE BANCO DE DADOS")
print("=" * 80)
print()


def print_section(title: str):
    """Imprime um cabecalho de secao"""
    print("\n" + "-" * 80)
    print(f"  {title}")
    print("-" * 80)


def print_result(test_name: str, success: bool, message: str = "", details: Dict[str, Any] = None):
    """Imprime o resultado de um teste"""
    status = "[OK] SUCESSO" if success else "[ERRO] FALHA"
    
    print(f"{status} - {test_name}")
    if message:
        print(f"  -> {message}")
    if details:
        for key, value in details.items():
            print(f"  * {key}: {value}")
    print()


async def test_sql_server_connection():
    """Testa conexão com SQL Server usando SQLAlchemy + aioodbc"""
    print_section("1. SQL SERVER (SQLAlchemy + aioodbc)")
    
    database_url = os.getenv("DATABASE_URL")
    use_sql_server = os.getenv("USE_SQL_SERVER", "false").lower() == "true"
    
    print(f"USE_SQL_SERVER: {use_sql_server}")
    print(f"DATABASE_URL: {database_url[:50]}..." if database_url else "DATABASE_URL: Não configurado")
    print()
    
    if not use_sql_server:
        print_result(
            "SQL Server",
            True,
            "SQL Server está desabilitado no .env (USE_SQL_SERVER=false)",
            {"Status": "Desabilitado intencionalmente"}
        )
        return
    
    if not database_url:
        print_result(
            "SQL Server",
            False,
            "DATABASE_URL não está configurado no .env"
        )
        return
    
    try:
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import text
        
        # Cria engine
        engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )
        
        # Testa conexão
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT @@VERSION as version"))
            version = result.scalar()
            
            # Testa query simples
            result = await conn.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
            
        await engine.dispose()
        
        print_result(
            "SQL Server",
            True,
            "Conexão estabelecida com sucesso",
            {
                "Versão": version[:100] if version else "N/A",
                "Teste Query": f"SELECT 1 = {test_value}"
            }
        )
        
    except ImportError as e:
        print_result(
            "SQL Server",
            False,
            f"Dependências não instaladas: {str(e)}",
            {"Solução": "pip install sqlalchemy[asyncio] aioodbc pyodbc"}
        )
    except Exception as e:
        print_result(
            "SQL Server",
            False,
            f"Erro ao conectar: {str(e)}",
            {"Tipo de Erro": type(e).__name__}
        )


async def test_pyodbc_connection():
    """Testa conexão direta com pyodbc/aioodbc"""
    print_section("2. SQL SERVER (pyodbc direto)")
    
    connection_string = os.getenv("PYODBC_CONNECTION_STRING")
    use_sql_server = os.getenv("USE_SQL_SERVER", "false").lower() == "true"
    
    print(f"PYODBC_CONNECTION_STRING: {connection_string[:50]}..." if connection_string else "Não configurado")
    print()
    
    if not use_sql_server:
        print_result(
            "pyodbc",
            True,
            "SQL Server está desabilitado no .env",
            {"Status": "Desabilitado intencionalmente"}
        )
        return
    
    if not connection_string:
        print_result(
            "pyodbc",
            False,
            "PYODBC_CONNECTION_STRING não está configurado no .env"
        )
        return
    
    try:
        import aioodbc
        
        # Testa conexão
        async with aioodbc.connect(dsn=connection_string, timeout=10) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT @@VERSION")
                version = await cursor.fetchone()
                
                await cursor.execute("SELECT DB_NAME()")
                db_name = await cursor.fetchone()
                
        print_result(
            "pyodbc",
            True,
            "Conexão estabelecida com sucesso",
            {
                "Versão": version[0][:100] if version else "N/A",
                "Database": db_name[0] if db_name else "N/A"
            }
        )
        
    except ImportError as e:
        print_result(
            "pyodbc",
            False,
            f"Dependências não instaladas: {str(e)}",
            {"Solução": "pip install aioodbc pyodbc"}
        )
    except Exception as e:
        print_result(
            "pyodbc",
            False,
            f"Erro ao conectar: {str(e)}",
            {"Tipo de Erro": type(e).__name__}
        )


async def test_supabase_connection():
    """Testa conexão com Supabase"""
    print_section("3. SUPABASE")
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    use_supabase = os.getenv("USE_SUPABASE_AUTH", "false").lower() == "true"
    
    print(f"USE_SUPABASE_AUTH: {use_supabase}")
    print(f"SUPABASE_URL: {supabase_url if supabase_url else 'Não configurado'}")
    print(f"SUPABASE_ANON_KEY: {'Configurado' if supabase_key else 'Não configurado'}")
    print()
    
    if not use_supabase:
        print_result(
            "Supabase",
            True,
            "Supabase está desabilitado no .env (USE_SUPABASE_AUTH=false)",
            {"Status": "Desabilitado intencionalmente"}
        )
        return
    
    if not supabase_url or not supabase_key:
        print_result(
            "Supabase",
            False,
            "SUPABASE_URL ou SUPABASE_ANON_KEY não estão configurados no .env"
        )
        return
    
    try:
        from supabase import create_client, Client
        
        # Cria cliente
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Testa conexão com uma query simples
        response = supabase.table("users").select("count", count="exact").limit(0).execute()
        
        print_result(
            "Supabase",
            True,
            "Conexão estabelecida com sucesso",
            {
                "URL": supabase_url,
                "Status": "Conectado"
            }
        )
        
    except ImportError as e:
        print_result(
            "Supabase",
            False,
            f"Dependências não instaladas: {str(e)}",
            {"Solução": "pip install supabase"}
        )
    except Exception as e:
        print_result(
            "Supabase",
            False,
            f"Erro ao conectar: {str(e)}",
            {"Tipo de Erro": type(e).__name__}
        )


async def test_parquet_files():
    """Testa acesso aos arquivos Parquet"""
    print_section("4. ARQUIVOS PARQUET")
    
    fallback_to_parquet = os.getenv("FALLBACK_TO_PARQUET", "true").lower() == "true"
    
    print(f"FALLBACK_TO_PARQUET: {fallback_to_parquet}")
    print()
    
    # Diretórios de dados
    data_dirs = [
        backend_dir / "data",
        backend_dir.parent / "data"
    ]
    
    parquet_files = []
    for data_dir in data_dirs:
        if data_dir.exists():
            parquet_files.extend(list(data_dir.glob("**/*.parquet")))
    
    if not parquet_files:
        print_result(
            "Parquet Files",
            False,
            "Nenhum arquivo .parquet encontrado nos diretórios de dados"
        )
        return
    
    try:
        import duckdb
        
        # Testa leitura de cada arquivo
        results = {}
        for parquet_file in parquet_files[:5]:  # Limita a 5 arquivos para não sobrecarregar
            try:
                conn = duckdb.connect(":memory:")
                result = conn.execute(f"SELECT COUNT(*) FROM '{parquet_file}'").fetchone()
                row_count = result[0] if result else 0
                
                # Pega informações das colunas
                columns = conn.execute(f"DESCRIBE SELECT * FROM '{parquet_file}'").fetchall()
                col_count = len(columns)
                
                conn.close()
                
                results[parquet_file.name] = {
                    "Linhas": row_count,
                    "Colunas": col_count,
                    "Status": "[OK]"
                }
            except Exception as e:
                results[parquet_file.name] = {
                    "Status": f"[ERRO] {str(e)[:50]}"
                }
        
        print_result(
            "Parquet Files",
            True,
            f"Encontrados {len(parquet_files)} arquivo(s) .parquet",
            results
        )
        
    except ImportError as e:
        print_result(
            "Parquet Files",
            False,
            f"Dependências não instaladas: {str(e)}",
            {"Solução": "pip install duckdb"}
        )
    except Exception as e:
        print_result(
            "Parquet Files",
            False,
            f"Erro ao ler arquivos: {str(e)}",
            {"Tipo de Erro": type(e).__name__}
        )


async def test_duckdb_connection():
    """Testa conexão com DuckDB"""
    print_section("5. DUCKDB (In-Memory)")
    
    try:
        import duckdb
        
        # Cria conexão em memória
        conn = duckdb.connect(":memory:")
        
        # Testa query simples
        result = conn.execute("SELECT 'DuckDB' as db, version() as version").fetchone()
        
        # Testa criação de tabela
        conn.execute("CREATE TABLE test (id INTEGER, name VARCHAR)")
        conn.execute("INSERT INTO test VALUES (1, 'Teste')")
        count = conn.execute("SELECT COUNT(*) FROM test").fetchone()[0]
        
        conn.close()
        
        print_result(
            "DuckDB",
            True,
            "Conexão estabelecida com sucesso",
            {
                "Versão": result[1] if result else "N/A",
                "Teste CRUD": f"Criou tabela e inseriu {count} registro(s)"
            }
        )
        
    except ImportError as e:
        print_result(
            "DuckDB",
            False,
            f"Dependências não instaladas: {str(e)}",
            {"Solução": "pip install duckdb"}
        )
    except Exception as e:
        print_result(
            "DuckDB",
            False,
            f"Erro ao conectar: {str(e)}",
            {"Tipo de Erro": type(e).__name__}
        )


async def main():
    """Executa todos os testes"""
    print("Iniciando testes de conexão...\n")
    
    # Executa todos os testes
    await test_sql_server_connection()
    await test_pyodbc_connection()
    await test_supabase_connection()
    await test_parquet_files()
    await test_duckdb_connection()
    
    print("\n" + "=" * 80)
    print("TESTES CONCLUÍDOS")
    print("=" * 80)
    print()
    print("Resumo da Configuração:")
    print(f"  • USE_SQL_SERVER: {os.getenv('USE_SQL_SERVER', 'false')}")
    print(f"  • FALLBACK_TO_PARQUET: {os.getenv('FALLBACK_TO_PARQUET', 'true')}")
    print(f"  • USE_SUPABASE_AUTH: {os.getenv('USE_SUPABASE_AUTH', 'false')}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
