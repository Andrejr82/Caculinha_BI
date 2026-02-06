"""
Load data from Parquet to SQL Server

MIGRATED TO DUCKDB (2025-12-31)
- Leitura de Parquet via DuckDB (mais rápido)
- SQL Server insert continua com pyodbc
- Conversão DuckDB -> Pandas -> SQL Server
"""
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter
import pyodbc
import numpy as np

print("\n" + "="*70)
print("  [CARREGAR DADOS DO PARQUET]")
print("="*70 + "\n")

parquet_file = Path(__file__).parent.parent / "data" / "parquet" / "admmat.parquet"

# Credenciais
server = r"FAMILIA\SQLJR,1433"
database = "agentbi"
username = "AgenteVirtual"
password = "Cacula@2020"
driver = "ODBC Driver 17 for SQL Server"

connection_string = (
    f"DRIVER={{{driver}}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    f"TrustServerCertificate=yes;"
)

try:
    print(f"[INFO] Lendo arquivo Parquet: {parquet_file}")

    # Use DuckDB for fast parquet reading
    adapter = get_duckdb_adapter()
    parquet_str = str(parquet_file.resolve()).replace("\\", "/")

    # Read with DuckDB and convert to Pandas for SQL Server compatibility
    df = adapter.query(f"""
        SELECT * FROM read_parquet('{parquet_str}')
    """)

    print(f"[OK] Arquivo lido via DuckDB. Linhas: {len(df)}")

    # Mapeamento de colunas (DataFrame -> Banco)
    # Ajustar nomes se necessário
    if 'estoque_atual' in df.columns:
        df['estoque_atual'] = df['estoque_atual'].fillna(0)
    if 'venda_30_d' in df.columns:
        df['venda_30_d'] = df['venda_30_d'].fillna(0)

    # Converter tipos para nativos do Python para evitar erro do pyodbc
    df = df.replace({np.nan: None})

    print("[INFO] Conectando ao banco...")
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    print("[INFO] Limpando tabela admmatao...")
    cursor.execute("TRUNCATE TABLE admmatao")
    conn.commit()

    print("[INFO] Inserindo dados (isso pode demorar)...")
    start_time = time.time()

    # Preparar query de insert
    insert_sql = """
    INSERT INTO admmatao (
        id, une, codigo, tipo, une_nome, nome_produto, embalagem,
        nomesegmento, nomecategoria, nomegrupo, nomesubgrupo, nomefabricante,
        ean, promocional, foralinha, venda_30_d, estoque_atual,
        estoque_cd, estoque_lojas, abc_une_mes_04, abc_une_mes_03,
        abc_une_mes_02, abc_une_mes_01, abc_une_30_dd
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    # Batch insert
    batch_size = 1000
    total_rows = len(df)

    for i in range(0, total_rows, batch_size):
        batch = df.iloc[i:i+batch_size]
        params = []

        for _, row in batch.iterrows():
            params.append((
                row.get('id'), row.get('une'), row.get('codigo'), row.get('tipo'),
                row.get('une_nome'), row.get('nome_produto'), row.get('embalagem'),
                row.get('nomesegmento'), row.get('NOMECATEGORIA'), row.get('nomegrupo'),
                row.get('NOMESUBGRUPO'), row.get('NOMEFABRICANTE'), row.get('ean'),
                row.get('promocional'), row.get('foralinha'), row.get('venda_30_d'),
                row.get('estoque_atual'), row.get('estoque_cd'),
                row.get('estoque_lv'),  # Mapeando estoque_lv para estoque_lojas
                row.get('abc_une_mes_04'), row.get('abc_une_mes_03'),
                row.get('abc_une_mes_02'), row.get('abc_une_mes_01'),
                row.get('abc_une_30_dd')
            ))

        cursor.executemany(insert_sql, params)
        conn.commit()

        if (i + batch_size) % 10000 == 0:
            print(f"  Processado: {i + batch_size}/{total_rows}")

    end_time = time.time()
    duration = end_time - start_time

    print(f"\n[OK] Carga concluída em {duration:.2f} segundos!")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"[ERROR] Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
