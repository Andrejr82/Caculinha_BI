"""
DuckDBVectorAdapter — Adapter de Busca Vetorial com DuckDB

Implementa VectorSearchPort usando DuckDB VSS para busca semântica.

Uso:
    from backend.infrastructure.adapters.vector import DuckDBVectorAdapter
    
    adapter = DuckDBVectorAdapter(db_path="vectors.duckdb")
    await adapter.index_message(message, embedding)
    results = await adapter.search_similar(query_embedding)

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

import json
from typing import Optional, List
from datetime import datetime
from pathlib import Path

import structlog

from backend.domain.ports.vector_search_port import VectorSearchPort
from backend.domain.entities.message import Message
from backend.domain.entities.memory_entry import MemoryEntry


logger = structlog.get_logger(__name__)


class DuckDBVectorAdapter(VectorSearchPort):
    """
    Adapter de busca vetorial usando DuckDB.
    
    Implementação de VectorSearchPort para busca por similaridade.
    Usa DuckDB com extensão VSS para busca vetorial eficiente.
    """
    
    def __init__(
        self,
        db_path: str = "vectors.duckdb",
        embedding_dimension: int = 768,
    ):
        """
        Inicializa o adapter DuckDB Vector.
        
        Args:
            db_path: Caminho para o arquivo DuckDB
            embedding_dimension: Dimensão dos embeddings
        """
        self.db_path = Path(db_path)
        self.embedding_dimension = embedding_dimension
        self._initialized = False
        self._conn = None
    
    def _get_connection(self):
        """Obtém conexão DuckDB."""
        if self._conn is None:
            try:
                import duckdb
                self._conn = duckdb.connect(str(self.db_path))
            except ImportError:
                logger.error("duckdb package not installed")
                raise
        return self._conn
    
    async def _ensure_tables(self):
        """Garante que as tabelas e índices existem."""
        if self._initialized:
            return
        
        conn = self._get_connection()
        
        # Cria tabela de memory entries
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS memory_entries (
                id VARCHAR PRIMARY KEY,
                conversation_id VARCHAR NOT NULL,
                message_id VARCHAR NOT NULL,
                tenant_id VARCHAR,
                content VARCHAR NOT NULL,
                embedding FLOAT[{self.embedding_dimension}],
                created_at TIMESTAMP NOT NULL,
                metadata VARCHAR
            )
        """)
        
        # Cria índices
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_conv 
            ON memory_entries(conversation_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_tenant 
            ON memory_entries(tenant_id)
        """)
        
        # Tenta carregar extensão VSS (pode não estar disponível)
        try:
            conn.execute("INSTALL vss")
            conn.execute("LOAD vss")
            logger.info("duckdb_vss_loaded")
        except Exception as e:
            logger.warning("vss_extension_not_available", error=str(e))
        
        self._initialized = True
        logger.info("duckdb_vector_tables_created", db_path=str(self.db_path))
    
    # =========================================================================
    # INDEXING OPERATIONS
    # =========================================================================
    
    async def index_message(
        self,
        message: Message,
        embedding: List[float],
    ) -> str:
        """Indexa uma mensagem com seu embedding."""
        await self._ensure_tables()
        
        entry = MemoryEntry.from_message(message, embedding)
        return await self.index_entry(entry)
    
    async def index_entry(self, entry: MemoryEntry) -> str:
        """Indexa uma entrada de memória."""
        await self._ensure_tables()
        
        conn = self._get_connection()
        
        # Extrai tenant_id do metadata se existir
        tenant_id = None
        if entry.metadata:
            tenant_id = entry.metadata.get("tenant_id")
        
        conn.execute("""
            INSERT OR REPLACE INTO memory_entries 
            (id, conversation_id, message_id, tenant_id, content, embedding, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.id,
            entry.conversation_id,
            entry.message_id,
            tenant_id,
            entry.content,
            entry.embedding if entry.embedding else None,
            entry.created_at,
            json.dumps(entry.metadata) if entry.metadata else None,
        ))
        
        logger.debug("memory_entry_indexed", entry_id=entry.id)
        return entry.id
    
    async def update_embedding(
        self,
        entry_id: str,
        embedding: List[float],
    ) -> bool:
        """Atualiza o embedding de uma entrada."""
        await self._ensure_tables()
        
        conn = self._get_connection()
        result = conn.execute("""
            UPDATE memory_entries 
            SET embedding = ?
            WHERE id = ?
        """, (embedding, entry_id))
        
        return result.rowcount > 0
    
    # =========================================================================
    # SEARCH OPERATIONS
    # =========================================================================
    
    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 5,
        tenant_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        min_score: float = 0.0,
    ) -> List[MemoryEntry]:
        """Busca mensagens similares por embedding usando distância coseno."""
        await self._ensure_tables()
        
        conn = self._get_connection()
        
        # Constrói query com filtros opcionais
        filters = []
        params = []
        
        if tenant_id:
            filters.append("tenant_id = ?")
            params.append(tenant_id)
        
        if conversation_id:
            filters.append("conversation_id = ?")
            params.append(conversation_id)
        
        where_clause = ""
        if filters:
            where_clause = "WHERE " + " AND ".join(filters)
        
        # Calcula similaridade coseno
        # score = 1 - distância (quanto maior, mais similar)
        query = f"""
            SELECT 
                id, conversation_id, message_id, content, 
                embedding, created_at, metadata,
                list_cosine_similarity(embedding, ?) as score
            FROM memory_entries
            {where_clause}
            {"AND" if where_clause else "WHERE"} embedding IS NOT NULL
            ORDER BY score DESC
            LIMIT ?
        """
        
        try:
            result = conn.execute(query, [query_embedding] + params + [limit])
            rows = result.fetchall()
        except Exception as e:
            # Fallback para busca sem VSS
            logger.warning("vector_search_fallback", error=str(e))
            query = f"""
                SELECT 
                    id, conversation_id, message_id, content, 
                    embedding, created_at, metadata,
                    0.5 as score
                FROM memory_entries
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            """
            result = conn.execute(query, params + [limit])
            rows = result.fetchall()
        
        entries = []
        for row in rows:
            score = row[7] if len(row) > 7 else 0.5
            if score >= min_score:
                entries.append(MemoryEntry(
                    id=row[0],
                    conversation_id=row[1],
                    message_id=row[2],
                    content=row[3],
                    embedding=row[4] if row[4] else [],
                    created_at=row[5],
                    metadata=json.loads(row[6]) if row[6] else None,
                    score=score,
                ))
        
        return entries
    
    async def search_by_content(
        self,
        query: str,
        limit: int = 5,
        tenant_id: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """Busca por texto com full-text search."""
        await self._ensure_tables()
        
        conn = self._get_connection()
        
        # Busca simples por LIKE (DuckDB suporta FTS com extensão)
        params = [f"%{query}%"]
        tenant_filter = ""
        if tenant_id:
            tenant_filter = "AND tenant_id = ?"
            params.append(tenant_id)
        
        result = conn.execute(f"""
            SELECT id, conversation_id, message_id, content, 
                   embedding, created_at, metadata
            FROM memory_entries
            WHERE content LIKE ? {tenant_filter}
            ORDER BY created_at DESC
            LIMIT ?
        """, params + [limit])
        
        rows = result.fetchall()
        return [
            MemoryEntry(
                id=row[0],
                conversation_id=row[1],
                message_id=row[2],
                content=row[3],
                embedding=row[4] if row[4] else [],
                created_at=row[5],
                metadata=json.loads(row[6]) if row[6] else None,
            )
            for row in rows
        ]
    
    # =========================================================================
    # MANAGEMENT OPERATIONS
    # =========================================================================
    
    async def delete_by_conversation(self, conversation_id: str) -> int:
        """Deleta todas as entradas de uma conversa."""
        await self._ensure_tables()
        
        conn = self._get_connection()
        result = conn.execute(
            "DELETE FROM memory_entries WHERE conversation_id = ?",
            (conversation_id,)
        )
        
        count = result.rowcount
        logger.info("memory_entries_deleted", conversation_id=conversation_id, count=count)
        return count
    
    async def delete_by_message(self, message_id: str) -> bool:
        """Deleta a entrada de uma mensagem específica."""
        await self._ensure_tables()
        
        conn = self._get_connection()
        result = conn.execute(
            "DELETE FROM memory_entries WHERE message_id = ?",
            (message_id,)
        )
        
        return result.rowcount > 0
    
    async def count_entries(
        self,
        tenant_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> int:
        """Conta entradas indexadas."""
        await self._ensure_tables()
        
        conn = self._get_connection()
        
        filters = []
        params = []
        
        if tenant_id:
            filters.append("tenant_id = ?")
            params.append(tenant_id)
        
        if conversation_id:
            filters.append("conversation_id = ?")
            params.append(conversation_id)
        
        where_clause = ""
        if filters:
            where_clause = "WHERE " + " AND ".join(filters)
        
        result = conn.execute(f"SELECT COUNT(*) FROM memory_entries {where_clause}", params)
        return result.fetchone()[0]
    
    async def get_stats(self) -> dict:
        """Retorna estatísticas do índice vetorial."""
        await self._ensure_tables()
        
        conn = self._get_connection()
        
        total = conn.execute("SELECT COUNT(*) FROM memory_entries").fetchone()[0]
        with_embedding = conn.execute(
            "SELECT COUNT(*) FROM memory_entries WHERE embedding IS NOT NULL"
        ).fetchone()[0]
        
        return {
            "total_entries": total,
            "entries_with_embedding": with_embedding,
            "embedding_dimension": self.embedding_dimension,
            "db_path": str(self.db_path),
        }
