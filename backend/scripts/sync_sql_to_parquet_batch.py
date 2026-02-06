"""
Sync SQL Server to Parquet - OTIMIZADO COM BATCHES
Extrai 1.1M+ linhas da tabela admmatao em batches para evitar timeout
"""
import pyodbc
import polars as pl
from pathlib import Path
import time

SERVER = "localhost,1433"
DATABASE = "Projeto_Caculinha"
USERNAME = "AgenteVirtual"
PASSWORD = "Cacula@2020"
DRIVER = "ODBC Driver 17 for SQL Server"
BATCH_SIZE = 100000  # 100k linhas por batch

CONNECTION_STRING = (
    f"DRIVER={{{DRIVER}}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"UID={USERNAME};"
    f"PWD={PASSWORD};"
    f"TrustServerCertificate=yes;"
)

TARGET_PATHS = [
    Path("../../data/parquet/admmat.parquet"),
    Path("../data/parquet/admmat.parquet"),
    Path("../app/data/parquet/admmat.parquet")
]

def sync_data():
    print("="*70)
    print("SINCRONIZAR SQL SERVER -> PARQUET (BATCH MODE)")
    print("="*70)

    start_time = time.time()

    try:
        print(f"\nConectando a {DATABASE}...")
        conn = pyodbc.connect(CONNECTION_STRING, timeout=30)
        cursor = conn.cursor()

        # Count total
        print("Contando linhas...")
        cursor.execute("SELECT COUNT(*) FROM admmatao")
        total_rows = cursor.fetchone()[0]
        print(f"Total a sincronizar: {total_rows:,} linhas")

        # Ler em batches usando OFFSET/FETCH
        all_dfs = []
        offset = 0

        while offset < total_rows:
            print(f"\nLendo batch {offset:,} - {min(offset+BATCH_SIZE, total_rows):,}...")

            query = f"""
            SELECT * FROM admmatao
            ORDER BY id
            OFFSET {offset} ROWS
            FETCH NEXT {BATCH_SIZE} ROWS ONLY
            """

            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]

            # Converter para Polars DataFrame
            df_batch = pl.DataFrame({col: [row[i] for row in rows] for i, col in enumerate(columns)})
            all_dfs.append(df_batch)

            print(f"  Lido: {len(rows):,} linhas")
            offset += BATCH_SIZE

        cursor.close()
        conn.close()

        # Concatenar todos os batches
        print("\nConcatenando batches...")
        df_final = pl.concat(all_dfs)
        print(f"Total final: {df_final.height:,} linhas x {df_final.width} colunas")

        # Salvar em todos os destinos
        for path in TARGET_PATHS:
            path.parent.mkdir(parents=True, exist_ok=True)
            print(f"\nSalvando: {path}")
            df_final.write_parquet(path)
            size_mb = path.stat().st_size / (1024*1024)
            print(f"  Tamanho: {size_mb:.2f} MB")

        end_time = time.time()
        print(f"\n{'='*70}")
        print(f"SUCESSO! Sincronizacao concluida em {end_time - start_time:.2f}s")
        print(f"{'='*70}\n")

    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    sync_data()
