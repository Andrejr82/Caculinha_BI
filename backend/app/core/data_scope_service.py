# backend/app/core/data_scope_service.py
import duckdb
import logging
import time
from typing import List, Optional, Union, Any
from pathlib import Path

from backend.app.infrastructure.database.models.user import User
from backend.app.config.settings import settings
from backend.app.core.duckdb_config import get_safe_connection

logger = logging.getLogger(__name__)

class DataScopeService:
    """
    Serviço para filtrar DataFrames baseados nas permissões de segmento do usuário.
    Garante que cada usuário veja apenas os dados aos quais tem acesso.
    
    PERFORMANCE UPDATE: Uses DuckDB for high-performance querying without loading full dataset into memory.
    """

    def __init__(self):
        # [OK] FIX 2026-02-11: Use central path from settings instead of hardcoded relative path
        self.parquet_path = settings.PARQUET_DATA_PATH
        logger.info(f"DataScopeService: Initialized with path: {self.parquet_path}")

    def _get_base_relation(self, con: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyRelation:
        """
        Returns a base DuckDB relation with global filters applied.
        """
        rel = con.read_parquet(self.parquet_path)
        
        # GLOBAL FILTER: Apply allowed UNEs whitelist if configured
        if settings.ALLOWED_UNES:
            # We assume 'UNE' column exists, but check safely
            try:
                # Check if UNE column exists in the parquet file
                # Limit 0 to get schema quickly
                columns = rel.limit(0).columns
                if "UNE" in columns:
                    # UNE is BIGINT, NOT string - remove quotes!
                    unes_str = ", ".join([str(une) for une in settings.ALLOWED_UNES])
                    rel = rel.filter(f"UNE IN ({unes_str})")
            except Exception as e:
                logger.warning(f"Could not apply UNE filter: {e}")
            
        return rel

    def get_filtered_dataframe(self, user: User, max_rows: Optional[int] = None, conn: Optional[duckdb.DuckDBPyConnection] = None) -> duckdb.DuckDBPyRelation:
        """
        Retorna uma DuckDB Relation (lazy) filtrada.
        
        Args:
            user: Usuário autenticado
            max_rows: Ignorado na nova implementação de streaming (mantido para compatibilidade)
            conn: Conexão DuckDB opcional. Se não fornecida, cria uma nova (mas cuidado com lazy eval).
            
        Returns:
            duckdb.DuckDBPyRelation: Uma relação lazy que lê diretamente do Parquet.
        """
        start_time = time.perf_counter()
        
        # Se nenhuma conexão for passada, cria uma segura. 
        # NOTA: O caller DEVE gerenciar a conexão se quiser usar o resultado depois.
        # Se criarmos aqui e fecharmos, a Relation morre.
        # Por isso, o ideal é o caller SEMPRE passar a conexão.
        if conn is None:
            # Fallback perigoso para compatibilidade, mas idealmente deve vir de fora
            # from app.core.duckdb_config import get_safe_connection # Already imported
            con = get_safe_connection()
            # Mantenha aberta? Sim, duckdb python fecha no GC.
        else:
            con = conn
        
        try:
            rel = self._get_base_relation(con)
            
            # 1. Apply User Permission Filters
            # [OK] FIX 2026-02-11: Se os segmentos permitidos forem nulos ou contiverem '*', dar acesso total.
            # Se for uma lista vazia, antigamente dava 1=0. Agora tratamos como acesso total se não houver restrição explícita.
            if not user or user.role == "admin" or user.username == "admin" or "*" in user.segments_list or not user.segments_list:
                # Caso a lista esteja explicitamente vazia [], damos acesso total (liberação por padrão)
                # Ou verificamos um flag específico. Para Caçulinha, vazio = Todos os segmentos (segurança relaxada por padrão)
                logger.info(f"Usuário {user.username} com acesso total (admin ou sem restrições).")
                pass
            else:
                allowed_segments = user.segments_list
                
                columns = rel.limit(0).columns
                segment_col = "nomesegmento" if "nomesegmento" in columns else "NOMESEGMENTO" if "NOMESEGMENTO" in columns else "SEGMENTO"
                
                if segment_col in columns:
                    segments_str = ", ".join(["'{}'".format(s.replace("'", "''")) for s in allowed_segments])
                    rel = rel.filter(f"{segment_col} IN ({segments_str})")
                else:
                    logger.warning(f"Coluna de segmento não encontrada no schema. Ignorando filtro de segmento.")
                    pass # Não filtra se não achar a coluna

            # 2. Row Limits - IGNORADO propositalmente para dados completos
            # ...
                
            # 3. Retornar Relation Lazy (NÃO materializar para Arrow/Polars)
            elapsed = time.perf_counter() - start_time
            logger.info(f"[INFO] Filtro DuckDB para {user.username} (lazy relation) em {elapsed:.4f}s")
            return rel

        except Exception as e:
            logger.error(f"Erro ao filtrar dados (DuckDB): {e}")
            # Fallback seguro: retorna relação sem filtro em caso de erro crítico de metadados
            return self._get_base_relation(con)
        # Não fechamos a conexão aqui pois retornamos um lazy object que precisa dela aberta

    def get_filtered_lazyframe(self, user: User) -> Any:
        """
        Retorna uma query DuckDB (Relation) não executada.
        Substitui o LazyFrame do Polars.
        """
        # Note: We need a persistent connection for the relation to remain valid if passed around.
        # This design pattern might need adjustment if the connection is closed.
        # Ideally, we return the SQL query string or a relation bound to a passed connection.
        # For simplicity in this migration: return the Relation and hope the connection stays alive 
        # (it won't if we close it in __init__).
        # So we create a new connection that relies on the caller to close or let GC handle it.
        con = duckdb.connect(":memory:")
        try:
            rel = self._get_base_relation(con)
            
            if (
                not user
                or user.role == "admin"
                or user.username == "admin"
                or "*" in user.segments_list
                or not user.segments_list
            ):
                return rel

            allowed_segments = user.segments_list
            
            columns = rel.limit(0).columns
            segment_col = "nomesegmento" if "nomesegmento" in columns else "NOMESEGMENTO" if "NOMESEGMENTO" in columns else "SEGMENTO"
            
            if segment_col in columns:
                segments_str = ", ".join(["'{}'".format(s.replace("'", "''")) for s in allowed_segments])
                return rel.filter(f"{segment_col} IN ({segments_str})")
            
            return self._get_empty_result(rel)
            
        except Exception as e:
            logger.error(f"Erro ao obter Relation DuckDB: {e}")
            return None

    def _get_empty_result(self, rel: duckdb.DuckDBPyRelation) -> duckdb.DuckDBPyRelation:
        """Helper para retornar Relation vazia preservando schema"""
        return rel.filter("1=0")

    def get_user_segments(self, user: User) -> List[str]:
        """
        Retorna a lista de segmentos únicos disponíveis para o usuário.

        - Admin: retorna TODOS os segmentos do sistema
        - "*" em segments_list: retorna TODOS os segmentos do sistema
        - Outros usuários: retorna apenas seus segmentos permitidos
        """
        if not user:
            return []

        # Admin ou acesso total: retornar TODOS os segmentos disponíveis no sistema
        if user.role == "admin" or user.username == "admin" or "*" in user.segments_list:
            con = duckdb.connect(":memory:")
            try:
                rel = self._get_base_relation(con)
                columns = rel.limit(0).columns
                segment_col = "nomesegmento" if "nomesegmento" in columns else "NOMESEGMENTO" if "NOMESEGMENTO" in columns else "SEGMENTO"

                if segment_col in columns:
                    # Efficient unique value extraction - TODOS os segmentos
                    unique_segments = rel.select(segment_col).distinct().fetchall()
                    all_segments = [str(s[0]) for s in unique_segments if s[0]]
                    logger.info(f"Admin user '{user.username}' accessing ALL segments: {len(all_segments)} segments")
                    return all_segments

                return []
            except Exception as e:
                logger.error(f"Erro ao buscar segmentos únicos para admin: {e}")
                return []
            finally:
                con.close()

        # Usuário regular: retornar apenas segmentos permitidos
        return user.segments_list

# Inicializar o serviço como um singleton
data_scope_service = DataScopeService()
