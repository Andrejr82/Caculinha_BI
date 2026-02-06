"""
Sync SQL Server to Parquet (Ajustado)
Extrai dados do SQL Server (tabela admmatao) e gera o arquivo admmat.parquet.
Garante que o Agente BI tenha dados atualizados e performantes.
"""
import pandas as pd
import pyodbc
import sys
import time
import os
from pathlib import Path

# Configurações extraídas do que funcionou no AuthService
SERVER = "127.0.0.1,1433"
DATABASE = "Projeto_Caculinha" # Banco com dados completos
USERNAME = "AgenteVirtual"
PASSWORD = "Cacula@2020"
DRIVER = "ODBC Driver 17 for SQL Server"

CONNECTION_STRING = (
    f"DRIVER={{{DRIVER}}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"UID={USERNAME};"
    f"PWD={PASSWORD};"
    f"TrustServerCertificate=yes;"
)

# Locais onde o sistema procura o parquet
TARGET_PATHS = [
    Path("data/parquet/admmat.parquet"),
    Path("backend/data/parquet/admmat.parquet")
]

def sync_data():
    print("\n" + "="*70)
    print("  SINCRONIZAR SQL SERVER -> PARQUET (BI DATA)")
    print("="*70 + "\n")

    start_time = time.time()

    try:
        print(f"Conectando ao SQL Server ({SERVER})...")
        conn = pyodbc.connect(CONNECTION_STRING)

        # Nota: Ajustar o nome da tabela se for diferente no banco agentbi
        query = "SELECT * FROM admmatao"
        print(f"Extraindo dados da tabela 'admmatao'...")

        # Leitura
        df = pd.read_sql(query, conn)
        conn.close()

        print(f"Extracao concluida. Total de linhas: {len(df)}")

        # Salvar em todos os destinos necessários
        for path in TARGET_PATHS:
            path.parent.mkdir(parents=True, exist_ok=True)
            print(f"Salvando: {path}")
            df.to_parquet(path, index=False)

        end_time = time.time()
        print(f"\nSincronizacao concluida com sucesso em {end_time - start_time:.2f}s!")

    except Exception as e:
        print(f"\nErro durante a sincronizacao: {e}")
        print("\nDica: Verifique se a tabela 'admmatao' existe no banco 'agentbi'.")
        sys.exit(1)

if __name__ == "__main__":
    sync_data()