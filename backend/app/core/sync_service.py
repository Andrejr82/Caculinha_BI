import pandas as pd
import pyodbc
import time
import logging
import os
from pathlib import Path
from app.config.settings import settings

logger = logging.getLogger(__name__)

class SyncService:
    """
    Serviço para sincronizar dados do SQL Server para arquivos Parquet.
    """

    def run_sync(self):
        """Executa a sincronização do admmat.parquet"""
        logger.info("[RETRY] Iniciando sincronização SQL Server -> Parquet...")
        start_time = time.time()

        try:
            # Usar connection string do settings ou montar uma
            if settings.PYODBC_CONNECTION_STRING:
                conn_str = settings.PYODBC_CONNECTION_STRING
            else:
                # Fallback para montagem manual (baseado no script antigo, mas usando vars do ambiente se disponiveis)
                driver = "ODBC Driver 17 for SQL Server"
                server = os.getenv("DB_SERVER", r"FAMILIA\SQLJR,1433")
                database = os.getenv("DB_NAME", "Projeto_Caculinha")
                uid = os.getenv("DB_USER", "AgenteVirtual")
                pwd = os.getenv("DB_PASS", "Cacula@2020")
                
                conn_str = (
                    f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};"
                    f"UID={uid};PWD={pwd};TrustServerCertificate=yes;"
                )

            logger.info(f"🔌 Conectando ao SQL Server... (Server: {conn_str.split('SERVER=')[1].split(';')[0]})")
            conn = pyodbc.connect(conn_str)
            
            # Query Principal
            query = "SELECT * FROM [Projeto_Caculinha].[dbo].[admmatao]"
            
            # Ler em chunks
            chunk_size = 100000
            chunks = []
            total_rows = 0
            
            for chunk in pd.read_sql(query, conn, chunksize=chunk_size):
                chunks.append(chunk)
                total_rows += len(chunk)
                logger.info(f"  ...Lido chunk de {len(chunk)} linhas. Total parcial: {total_rows}")
            
            conn.close()
            logger.info(f"[OK] Leitura SQL concluída. Total: {total_rows}")

            if not chunks:
                logger.warning("[WARNING] Nenhum dado retornado do banco.")
                return {"status": "warning", "message": "Nenhum dado encontrado"}

            logger.info("🔨 Concatenando DataFrames...")
            df = pd.concat(chunks, ignore_index=True)
            
            # Definir caminho do arquivo (local)
            base_path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "parquet"
            
            base_path.mkdir(parents=True, exist_ok=True)
            parquet_file = base_path / "admmat.parquet"

            logger.info(f"💾 Salvando Parquet: {parquet_file}")
            df.to_parquet(parquet_file, index=False)
            
            # Limpar cache do Polars (se houver mecanismo de invalidação)
            from app.core.parquet_cache import cache
            cache.clear()
            
            duration = time.time() - start_time
            logger.info(f"[OK] Sincronização concluída em {duration:.2f}s")
            
            return {
                "status": "success", 
                "rows": total_rows, 
                "duration": duration,
                "file": str(parquet_file)
            }

        except Exception as e:
            logger.error(f"[ERROR] Erro na sincronização: {e}", exc_info=True)
            raise e

sync_service = SyncService()
