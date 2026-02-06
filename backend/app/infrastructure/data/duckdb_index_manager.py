"""
DuckDB Index Manager - Criação e Gerenciamento de Índices

Implementa índices para otimização de queries (10-100x speedup).
Baseado nas recomendações do Database Architect.
"""

import duckdb
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PARQUET_FILE = PROJECT_ROOT / "data" / "parquet" / "admmat.parquet"
DUCKDB_FILE = PROJECT_ROOT / "data" / "admmat.duckdb"


class DuckDBIndexManager:
    """
    Gerenciador de índices DuckDB para otimização de queries.
    
    Features:
    - Criação automática de índices
    - Migração de Parquet para DuckDB
    - Análise de query plans
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Inicializa o gerenciador de índices.
        
        Args:
            db_path: Caminho para o arquivo DuckDB (default: admmat.duckdb)
        """
        self.db_path = db_path or DUCKDB_FILE
        self.parquet_path = PARQUET_FILE
        
    def create_indexed_database(self) -> bool:
        """
        Cria banco DuckDB com índices a partir do Parquet.
        
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            logger.info(f"Criando banco DuckDB com índices: {self.db_path}")
            
            # Conectar ao DuckDB
            conn = duckdb.connect(str(self.db_path))
            
            # 1. Importar dados do Parquet
            logger.info(f"Importando dados de {self.parquet_path}...")
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS admmat AS 
                SELECT * FROM read_parquet('{self.parquet_path}')
            """)
            
            # Verificar quantas linhas foram importadas
            count = conn.execute("SELECT COUNT(*) FROM admmat").fetchone()[0]
            logger.info(f"[OK] {count:,} linhas importadas")
            
            # 2. Criar índices nas colunas mais consultadas
            indexes = [
                ("idx_produto", "PRODUTO"),
                ("idx_une", "UNE"),
                ("idx_segmento", "NOMESEGMENTO"),
                ("idx_produto_une", "PRODUTO, UNE"),  # Índice composto
            ]
            
            for idx_name, columns in indexes:
                try:
                    logger.info(f"Criando índice {idx_name} em ({columns})...")
                    conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON admmat({columns})")
                    logger.info(f"[OK] Índice {idx_name} criado")
                except Exception as e:
                    logger.warning(f"[WARNING] Erro ao criar índice {idx_name}: {e}")
            
            # 3. Analisar tabela para otimizar query planner
            logger.info("Analisando tabela para otimização...")
            conn.execute("ANALYZE admmat")
            
            # 4. Verificar índices criados
            indexes_info = conn.execute("""
                SELECT index_name, column_names 
                FROM duckdb_indexes() 
                WHERE table_name = 'admmat'
            """).fetchall()
            
            logger.info(f"[OK] {len(indexes_info)} índices criados:")
            for idx_name, cols in indexes_info:
                logger.info(f"  - {idx_name}: {cols}")
            
            conn.close()
            
            logger.info(f"[OK] Banco DuckDB criado com sucesso: {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Erro ao criar banco DuckDB: {e}", exc_info=True)
            return False
    
    def analyze_query(self, query: str) -> dict:
        """
        Analisa o plano de execução de uma query.
        
        Args:
            query: Query SQL para analisar
            
        Returns:
            Dicionário com informações do plano de execução
        """
        try:
            conn = duckdb.connect(str(self.db_path), read_only=True)
            
            # EXPLAIN ANALYZE
            plan = conn.execute(f"EXPLAIN ANALYZE {query}").fetchall()
            
            conn.close()
            
            return {
                "query": query,
                "plan": plan,
                "uses_index": any("INDEX_SCAN" in str(row) for row in plan)
            }
            
        except Exception as e:
            logger.error(f"Erro ao analisar query: {e}")
            return {"error": str(e)}
    
    def get_index_stats(self) -> List[dict]:
        """
        Retorna estatísticas dos índices.
        
        Returns:
            Lista de dicionários com informações dos índices
        """
        try:
            conn = duckdb.connect(str(self.db_path), read_only=True)
            
            stats = conn.execute("""
                SELECT 
                    index_name,
                    table_name,
                    column_names,
                    is_unique,
                    is_primary
                FROM duckdb_indexes()
                WHERE table_name = 'admmat'
            """).fetchall()
            
            conn.close()
            
            return [
                {
                    "index_name": row[0],
                    "table_name": row[1],
                    "columns": row[2],
                    "is_unique": row[3],
                    "is_primary": row[4]
                }
                for row in stats
            ]
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return []


def create_indexes_if_needed():
    """
    Função helper para criar índices se o banco não existir.
    
    Returns:
        Path para o banco DuckDB
    """
    manager = DuckDBIndexManager()
    
    if not manager.db_path.exists():
        logger.info("Banco DuckDB não encontrado. Criando com índices...")
        success = manager.create_indexed_database()
        
        if success:
            logger.info("[OK] Banco DuckDB criado com índices!")
        else:
            logger.error("[ERROR] Falha ao criar banco DuckDB")
            raise RuntimeError("Não foi possível criar banco DuckDB com índices")
    else:
        logger.info(f"[OK] Banco DuckDB já existe: {manager.db_path}")
    
    return manager.db_path


if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Criar índices
    manager = DuckDBIndexManager()
    success = manager.create_indexed_database()
    
    if success:
        # Mostrar estatísticas
        stats = manager.get_index_stats()
        print("\n[DATA] Índices Criados:")
        for stat in stats:
            print(f"  - {stat['index_name']}: {stat['columns']}")
        
        # Testar query
        test_query = "SELECT * FROM admmat WHERE PRODUTO = '59294'"
        analysis = manager.analyze_query(test_query)
        print(f"\n[SEARCH] Análise de Query:")
        print(f"  Usa índice: {analysis.get('uses_index', False)}")
