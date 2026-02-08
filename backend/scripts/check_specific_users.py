"""
Check specific users in SQL Server and Parquet

MIGRATED TO DUCKDB (2025-12-31)
- Parquet queries via DuckDB SQL (faster)
- SQL Server queries unchanged (pyodbc)
"""

import pyodbc
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter

# Configurações
CONN_STR = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;DATABASE=agentbi;UID=AgenteVirtual;PWD=Cacula@2020;TrustServerCertificate=yes;"
PARQUET_PATH = Path("backend/data/parquet/users.parquet")
USERS_TO_CHECK = ["lucas.garcia", "hugo.mendes", "fausto.neto"]


def check_sql():
    print("--- Verificando SQL Server ---")
    try:
        conn = pyodbc.connect(CONN_STR)
        cursor = conn.cursor()
        for user in USERS_TO_CHECK:
            cursor.execute("SELECT username, role, is_active FROM users WHERE username = ?", (user,))
            row = cursor.fetchone()
            if row:
                print(f"[OK] Usuário '{user}' encontrado! (Role: {row[1]}, Ativo: {row[2]})")
            else:
                print(f"[NOT FOUND] Usuário '{user}' NÃO encontrado.")
        conn.close()
    except Exception as e:
        print(f"[ERROR] Erro no SQL Server: {e}")


def check_parquet():
    print("\n--- Verificando Parquet ---")
    if not PARQUET_PATH.exists():
        print(f"[ERROR] Arquivo {PARQUET_PATH} não encontrado.")
        return

    try:
        adapter = get_duckdb_adapter()
        parquet_str = str(PARQUET_PATH.resolve()).replace("\\", "/")

        for user in USERS_TO_CHECK:
            # Query DuckDB for specific user
            result = adapter.connection.execute(f"""
                SELECT username, role, is_active
                FROM read_parquet('{parquet_str}')
                WHERE username = ?
            """, [user]).fetchall()

            if result and len(result) > 0:
                row = result[0]
                print(f"[OK] Usuário '{user}' encontrado! (Role: {row[1]}, Ativo: {row[2]})")
            else:
                print(f"[NOT FOUND] Usuário '{user}' NÃO encontrado.")
    except Exception as e:
        print(f"[ERROR] Erro no Parquet: {e}")


if __name__ == "__main__":
    check_sql()
    check_parquet()
