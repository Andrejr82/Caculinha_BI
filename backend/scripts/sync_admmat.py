"""
Script de Migração: SQL Server -> Parquet (admmat.parquet)
----------------------------------------------------------
Este script sincroniza os dados da tabela 'admmatao' do SQL Server para o arquivo
'admmat.parquet', fornecendo uma interface visual de progresso.

Funcionalidades:
- Conexão segura via ODBC
- Leitura em chunks para eficiência de memória
- Barra de progresso visual (tqdm)
- Estatísticas finais de migração
"""
import pandas as pd
import pyodbc
import sys
import time
import os
from pathlib import Path
from tqdm import tqdm
from sqlalchemy import create_engine
import warnings

# Suprimir avisos do pandas/sqlalchemy se houver
warnings.filterwarnings('ignore')

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configurações
PARQUET_FILE = Path(__file__).parent.parent / "data" / "parquet" / "admmat.parquet"
SERVER = r"FAMILIA\SQLJR,1433"
DATABASE = "Projeto_Caculinha"
USERNAME = "AgenteVirtual"
PASSWORD = "Cacula@2020"
DRIVER = "ODBC Driver 17 for SQL Server"
TABLE_NAME = "[Projeto_Caculinha].[dbo].[admmatao]"

CONNECTION_STRING = (
    f"DRIVER={{{DRIVER}}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"UID={USERNAME};"
    f"PWD={PASSWORD};"
    f"TrustServerCertificate=yes;"
)

def get_row_count(conn):
    """Obtém o número total de linhas na tabela para a barra de progresso."""
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        print(f"⚠️  Aviso: Não foi possível obter contagem total: {e}")
        return None

def sync_data():
    print("\n" + "="*70)
    print("  🚀 INICIANDO MIGRAÇÃO: SQL SERVER -> ADMMAT.PARQUET")
    print("="*70 + "\n")

    start_time = time.time()

    try:
        print(f"🔌 Conectando ao SQL Server em {SERVER}...")
        conn = pyodbc.connect(CONNECTION_STRING)
        
        # Obter total de linhas para barra de progresso
        total_rows = get_row_count(conn)
        print(f"📊 Total de registros encontrados: {total_rows if total_rows else 'Desconhecido'}")
        
        # Configurar leitura em chunks
        chunk_size = 50000
        query = f"SELECT * FROM {TABLE_NAME}"
        

        rows_processed = 0
        
        # Inicializar barra de progresso
        pbar = tqdm(total=total_rows, unit='rows', desc="⏳ Sincronizando")
        
        # Garantir diretório
        PARQUET_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Iterar sobre os chunks e salvar imediatamente
        first_chunk = True
        for chunk in pd.read_sql(query, conn, chunksize=chunk_size):
            if first_chunk:
                # Primeiro chunk: sobrescreve/cria o arquivo
                chunk.to_parquet(PARQUET_FILE, index=False, engine='fastparquet')
                first_chunk = False
            else:
                # Chunks subsequentes: append
                chunk.to_parquet(PARQUET_FILE, index=False, engine='fastparquet', append=True)
            
            rows_processed += len(chunk)
            pbar.update(len(chunk))
            
        pbar.close()
        conn.close()
        
        print("\n✅ Leitura e gravação concluída.")

        if rows_processed == 0:
            print("⚠️  Nenhum dado encontrado na tabela de origem.")
            return

        end_time = time.time()
        duration = end_time - start_time
        
        # Estatísticas finais
        print("\n" + "="*70)
        print("  🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*70)
        print(f"⏱️  Tempo total: {duration:.2f} segundos")
        print(f"📥 Registros migrados: {rows_processed}")
        print(f"📂 Destino: {PARQUET_FILE}")
        print(f"📏 Tamanho do arquivo: {PARQUET_FILE.stat().st_size / (1024*1024):.2f} MB")
        
    except Exception as e:
        print(f"\n❌ ERRO FATAL: Falha durante a migração: {e}")
        sys.exit(1)

if __name__ == "__main__":
    sync_data()
