"""
Script de Teste de Conexoes - Gera Relatorio HTML
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any
from datetime import datetime
import json

# Adiciona o diretorio backend ao path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Carrega variaveis de ambiente
load_dotenv(backend_dir / ".env")

# Armazena resultados
test_results = []


def add_result(category: str, test_name: str, success: bool, message: str = "", details: Dict[str, Any] = None):
    """Adiciona um resultado ao relatorio"""
    test_results.append({
        "category": category,
        "test_name": test_name,
        "success": success,
        "message": message,
        "details": details or {}
    })
    
    # Tambem imprime no console
    status = "[OK]" if success else "[ERRO]"
    print(f"{status} {category} - {test_name}")
    if message:
        print(f"  {message}")


async def test_sql_server_connection():
    """Testa conexao com SQL Server"""
    print("\n=== SQL SERVER (SQLAlchemy + aioodbc) ===")
    
    database_url = os.getenv("DATABASE_URL")
    use_sql_server = os.getenv("USE_SQL_SERVER", "false").lower() == "true"
    
    if not use_sql_server:
        add_result("SQL Server", "Configuracao", True, "Desabilitado no .env (USE_SQL_SERVER=false)")
        return
    
    if not database_url:
        add_result("SQL Server", "Configuracao", False, "DATABASE_URL nao configurado")
        return
    
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        engine = create_async_engine(database_url, echo=False, pool_pre_ping=True)
        
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT @@VERSION as version"))
            version = result.scalar()
            
            result = await conn.execute(text("SELECT DB_NAME() as dbname"))
            dbname = result.scalar()
            
        await engine.dispose()
        
        add_result("SQL Server", "Conexao", True, "Conectado com sucesso", {
            "Database": dbname,
            "Versao": version[:80] if version else "N/A"
        })
        
    except ImportError as e:
        add_result("SQL Server", "Dependencias", False, f"Modulos nao instalados: {str(e)}")
    except Exception as e:
        add_result("SQL Server", "Conexao", False, f"Erro: {str(e)}")


async def test_supabase_connection():
    """Testa conexao com Supabase"""
    print("\n=== SUPABASE ===")
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    use_supabase = os.getenv("USE_SUPABASE_AUTH", "false").lower() == "true"
    
    if not use_supabase:
        add_result("Supabase", "Configuracao", True, "Desabilitado no .env (USE_SUPABASE_AUTH=false)")
        return
    
    if not supabase_url or not supabase_key:
        add_result("Supabase", "Configuracao", False, "SUPABASE_URL ou SUPABASE_ANON_KEY nao configurados")
        return
    
    try:
        from supabase import create_client
        
        supabase = create_client(supabase_url, supabase_key)
        response = supabase.table("users").select("count", count="exact").limit(0).execute()
        
        add_result("Supabase", "Conexao", True, "Conectado com sucesso", {
            "URL": supabase_url,
            "Tabela users": "Acessivel"
        })
        
    except ImportError as e:
        add_result("Supabase", "Dependencias", False, f"Modulos nao instalados: {str(e)}")
    except Exception as e:
        add_result("Supabase", "Conexao", False, f"Erro: {str(e)}")


async def test_parquet_files():
    """Testa acesso aos arquivos Parquet"""
    print("\n=== ARQUIVOS PARQUET ===")
    
    data_dirs = [backend_dir / "data", backend_dir.parent / "data"]
    parquet_files = []
    
    for data_dir in data_dirs:
        if data_dir.exists():
            parquet_files.extend(list(data_dir.glob("**/*.parquet")))
    
    if not parquet_files:
        add_result("Parquet", "Arquivos", False, "Nenhum arquivo .parquet encontrado")
        return
    
    try:
        import duckdb
        
        files_info = {}
        for parquet_file in parquet_files[:10]:
            try:
                conn = duckdb.connect(":memory:")
                result = conn.execute(f"SELECT COUNT(*) FROM '{parquet_file}'").fetchone()
                row_count = result[0] if result else 0
                
                columns = conn.execute(f"DESCRIBE SELECT * FROM '{parquet_file}'").fetchall()
                col_count = len(columns)
                
                conn.close()
                
                files_info[parquet_file.name] = f"{row_count} linhas, {col_count} colunas"
            except Exception as e:
                files_info[parquet_file.name] = f"Erro: {str(e)[:30]}"
        
        add_result("Parquet", "Leitura", True, f"Encontrados {len(parquet_files)} arquivos", files_info)
        
    except ImportError as e:
        add_result("Parquet", "Dependencias", False, f"Modulos nao instalados: {str(e)}")
    except Exception as e:
        add_result("Parquet", "Leitura", False, f"Erro: {str(e)}")


async def test_duckdb_connection():
    """Testa conexao com DuckDB"""
    print("\n=== DUCKDB ===")
    
    try:
        import duckdb
        
        conn = duckdb.connect(":memory:")
        result = conn.execute("SELECT version() as version").fetchone()
        version = result[0] if result else "N/A"
        
        conn.execute("CREATE TABLE test (id INTEGER, name VARCHAR)")
        conn.execute("INSERT INTO test VALUES (1, 'Teste')")
        count = conn.execute("SELECT COUNT(*) FROM test").fetchone()[0]
        
        conn.close()
        
        add_result("DuckDB", "Conexao", True, "Funcionando corretamente", {
            "Versao": version,
            "Teste CRUD": f"Inseriu {count} registro(s)"
        })
        
    except ImportError as e:
        add_result("DuckDB", "Dependencias", False, f"Modulos nao instalados: {str(e)}")
    except Exception as e:
        add_result("DuckDB", "Conexao", False, f"Erro: {str(e)}")


def generate_html_report():
    """Gera relatorio HTML"""
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatorio de Testes de Conexao - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2em; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .summary-card h3 {{ color: #666; font-size: 0.9em; margin-bottom: 10px; }}
        .summary-card .value {{ font-size: 2em; font-weight: bold; }}
        .summary-card.success .value {{ color: #28a745; }}
        .summary-card.error .value {{ color: #dc3545; }}
        .summary-card.total .value {{ color: #667eea; }}
        .content {{ padding: 30px; }}
        .test-category {{
            margin-bottom: 30px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
        }}
        .category-header {{
            background: #667eea;
            color: white;
            padding: 15px 20px;
            font-size: 1.2em;
            font-weight: bold;
        }}
        .test-item {{
            padding: 20px;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            align-items: flex-start;
            gap: 15px;
        }}
        .test-item:last-child {{ border-bottom: none; }}
        .test-item:hover {{ background: #f8f9fa; }}
        .status-icon {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5em;
            flex-shrink: 0;
        }}
        .status-icon.success {{ background: #d4edda; color: #28a745; }}
        .status-icon.error {{ background: #f8d7da; color: #dc3545; }}
        .test-info {{ flex: 1; }}
        .test-name {{ font-weight: bold; font-size: 1.1em; margin-bottom: 5px; }}
        .test-message {{ color: #666; margin-bottom: 10px; }}
        .test-details {{
            background: #f8f9fa;
            padding: 10px 15px;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        .test-details div {{ margin: 5px 0; }}
        .test-details strong {{ color: #667eea; }}
        .config-section {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-top: 30px;
        }}
        .config-section h3 {{ margin-bottom: 15px; color: #333; }}
        .config-item {{ 
            padding: 8px 0;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
        }}
        .config-item:last-child {{ border-bottom: none; }}
        .config-key {{ font-weight: bold; color: #667eea; }}
        .config-value {{ color: #666; font-family: 'Courier New', monospace; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Relatorio de Testes de Conexao</h1>
            <p>Gerado em: {datetime.now().strftime('%d/%m/%Y as %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card total">
                <h3>Total de Testes</h3>
                <div class="value">{len(test_results)}</div>
            </div>
            <div class="summary-card success">
                <h3>Sucessos</h3>
                <div class="value">{sum(1 for r in test_results if r['success'])}</div>
            </div>
            <div class="summary-card error">
                <h3>Falhas</h3>
                <div class="value">{sum(1 for r in test_results if not r['success'])}</div>
            </div>
        </div>
        
        <div class="content">
"""
    
    # Agrupa resultados por categoria
    categories = {}
    for result in test_results:
        cat = result['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(result)
    
    # Gera HTML para cada categoria
    for category, results in categories.items():
        html += f"""
            <div class="test-category">
                <div class="category-header">{category}</div>
"""
        for result in results:
            status_class = "success" if result['success'] else "error"
            status_icon = "✓" if result['success'] else "✗"
            
            html += f"""
                <div class="test-item">
                    <div class="status-icon {status_class}">{status_icon}</div>
                    <div class="test-info">
                        <div class="test-name">{result['test_name']}</div>
"""
            if result['message']:
                html += f"""                        <div class="test-message">{result['message']}</div>\n"""
            
            if result['details']:
                html += """                        <div class="test-details">\n"""
                for key, value in result['details'].items():
                    html += f"""                            <div><strong>{key}:</strong> {value}</div>\n"""
                html += """                        </div>\n"""
            
            html += """                    </div>
                </div>
"""
        html += """            </div>\n"""
    
    # Adiciona configuracao do .env
    html += f"""
            <div class="config-section">
                <h3>Configuracao do .env</h3>
                <div class="config-item">
                    <span class="config-key">USE_SQL_SERVER</span>
                    <span class="config-value">{os.getenv('USE_SQL_SERVER', 'false')}</span>
                </div>
                <div class="config-item">
                    <span class="config-key">FALLBACK_TO_PARQUET</span>
                    <span class="config-value">{os.getenv('FALLBACK_TO_PARQUET', 'true')}</span>
                </div>
                <div class="config-item">
                    <span class="config-key">USE_SUPABASE_AUTH</span>
                    <span class="config-value">{os.getenv('USE_SUPABASE_AUTH', 'false')}</span>
                </div>
                <div class="config-item">
                    <span class="config-key">LLM_PROVIDER</span>
                    <span class="config-value">{os.getenv('LLM_PROVIDER', 'N/A')}</span>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    # Salva o relatorio
    report_path = backend_dir / "test_db_report.html"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"\n{'='*80}")
    print(f"Relatorio HTML gerado: {report_path}")
    print(f"{'='*80}\n")
    
    return report_path


async def main():
    """Executa todos os testes"""
    print("="*80)
    print("TESTE DE CONEXOES DE BANCO DE DADOS")
    print("="*80)
    
    await test_sql_server_connection()
    await test_supabase_connection()
    await test_parquet_files()
    await test_duckdb_connection()
    
    report_path = generate_html_report()
    
    # Abre o relatorio no navegador
    import webbrowser
    webbrowser.open(str(report_path))


if __name__ == "__main__":
    asyncio.run(main())
