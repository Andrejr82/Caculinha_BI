"""
DuckDBVectorAdapter — Adapter de Busca Vetorial DuckDB

Implementação de busca semântica usando DuckDB com VSS.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

import json
from typing import List, Optional, Tuple
from pathlib import Path
from datetime import datetime

import duckdb
import structlog

from backend.domain.ports.vector_repository_port import IVectorRepository
from backend.domain.entities.memory_entry import MemoryEntry
from backend.domain.entities.document import Document
from backend.domain.entities.embedding import Embedding


logger = structlog.get_logger(__name__)


class DuckDBVectorAdapter(IVectorRepository):
    """
    Adapter DuckDB para busca vetorial.
    
    Usa DuckDB com extensão VSS para busca por similaridade.
    Ideal para: busca semântica, RAG, memória de longo prazo.
    """
    
    def __init__(
        self, 
        db_path: str = "data/vectors.duckdb",
        dimension: int = 768,
    ):
        """
        Inicializa o adapter DuckDB.
        
        Args:
            db_path: Caminho para o arquivo do banco
            dimension: Dimensão dos vetores (768 para Gemini)
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.dimension = dimension
        self._initialized = False
        self._conn = None
    
    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """Obtém conexão com o banco."""
        if self._conn is None:
            self._conn = duckdb.connect(str(self.db_path))
        return self._conn
    
    async def _ensure_initialized(self):
        """Garante que as tabelas existem."""
        if self._initialized:
            return
        
        conn = self._get_connection()
        
        # Cria tabela de memórias
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS memory_entries (
                id VARCHAR PRIMARY KEY,
                conversation_id VARCHAR NOT NULL,
                message_id VARCHAR,
                content TEXT NOT NULL,
                embedding FLOAT[{self.dimension}],
                score FLOAT DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSON
            )
        """)
        
        # Cria tabela de documentos
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS document_embeddings (
                id VARCHAR PRIMARY KEY,
                document_id VARCHAR NOT NULL,
                tenant_id VARCHAR NOT NULL,
                content TEXT NOT NULL,
                embedding FLOAT[{self.dimension}],
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSON
            )
        """)
        
        # Cria índices
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_mem_conv 
            ON memory_entries(conversation_id)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_doc_tenant 
            ON document_embeddings(tenant_id)
        """)
        
        self._initialized = True
        logger.info("duckdb_vector_initialized", db_path=str(self.db_path))
    
    # =========================================================================
    # INDEXING OPERATIONS
    # =========================================================================
    
    async def index_entry(self, entry: MemoryEntry) -> str:
        """Indexa uma entrada de memória."""
        await self._ensure_initialized()
        conn = self._get_connection()
        
        embedding_str = str(entry.embedding) if entry.embedding else "NULL"
        
        # Delete existing then insert (DuckDB não suporta INSERT OR REPLACE)
        conn.execute("DELETE FROM memory_entries WHERE id = ?", [entry.id])
        conn.execute("""
            INSERT INTO memory_entries 
            (id, conversation_id, message_id, content, embedding, score, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            entry.id,
            entry.conversation_id,
            entry.message_id,
            entry.content,
            entry.embedding,
            entry.score,
            entry.created_at,
            json.dumps(entry.metadata) if entry.metadata else None,
        ])
        
        return entry.id
    
    async def index_document(self, document: Document, embedding: Embedding) -> str:
        """Indexa um documento com seu embedding."""
        await self._ensure_initialized()
        conn = self._get_connection()
        
        # Delete existing then insert
        conn.execute("DELETE FROM document_embeddings WHERE id = ?", [embedding.id])
        conn.execute("""
            INSERT INTO document_embeddings 
            (id, document_id, tenant_id, content, embedding, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            embedding.id,
            document.id,
            document.tenant_id,
            document.content,
            embedding.vector,
            document.created_at,
            json.dumps(document.metadata) if document.metadata else None,
        ])
        
        return embedding.id
    
    async def batch_index(self, entries: List[MemoryEntry]) -> List[str]:
        """Indexa múltiplas entradas em lote."""
        ids = []
        for entry in entries:
            id = await self.index_entry(entry)
            ids.append(id)
        return ids
    
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
        """Busca entradas similares por embedding."""
        await self._ensure_initialized()
        conn = self._get_connection()
        
        # Constrói query com filtros
        where_clauses = ["embedding IS NOT NULL"]
        params = []
        
        if conversation_id:
            where_clauses.append("conversation_id = ?")
            params.append(conversation_id)
        
        where_sql = " AND ".join(where_clauses)
        
        # Busca com similaridade de cosseno
        # DuckDB usa list_cosine_similarity para vetores
        query = f"""
            SELECT 
                id, conversation_id, message_id, content, 
                embedding, score, created_at, metadata,
                list_cosine_similarity(embedding, ?::FLOAT[{self.dimension}]) as similarity
            FROM memory_entries
            WHERE {where_sql}
            ORDER BY similarity DESC
            LIMIT ?
        """
        
        result = conn.execute(query, [query_embedding] + params + [limit]).fetchall()
        
        entries = []
        for row in result:
            similarity = row[8] if row[8] else 0.0
            if similarity >= min_score:
                entries.append(MemoryEntry(
                    id=row[0],
                    conversation_id=row[1],
                    message_id=row[2],
                    content=row[3],
                    embedding=row[4],
                    score=similarity,
                    created_at=row[6],
                    metadata=json.loads(row[7]) if row[7] else None,
                ))
        
        return entries
    
    async def search_by_content(
        self,
        query: str,
        limit: int = 5,
        tenant_id: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """Busca por conteúdo textual (fallback sem embedding)."""
        await self._ensure_initialized()
        conn = self._get_connection()
        
        # Busca simples por LIKE (fallback)
        result = conn.execute("""
            SELECT id, conversation_id, message_id, content, 
                   embedding, score, created_at, metadata
            FROM memory_entries
            WHERE content ILIKE ?
            LIMIT ?
        """, [f"%{query}%", limit]).fetchall()
        
        return [
            MemoryEntry(
                id=row[0],
                conversation_id=row[1],
                message_id=row[2],
                content=row[3],
                embedding=row[4],
                score=0.5,  # Score fixo para busca textual
                created_at=row[6],
                metadata=json.loads(row[7]) if row[7] else None,
            )
            for row in result
        ]
    
    async def hybrid_search(
        self,
        query: str,
        query_embedding: List[float],
        limit: int = 5,
        tenant_id: Optional[str] = None,
        alpha: float = 0.5,
    ) -> List[Tuple[MemoryEntry, float]]:
        """Busca híbrida (textual + vetorial)."""
        # Busca vetorial
        vector_results = await self.search_similar(
            query_embedding, limit=limit * 2, tenant_id=tenant_id
        )
        
        # Busca textual
        text_results = await self.search_by_content(
            query, limit=limit * 2, tenant_id=tenant_id
        )
        
        # Combina resultados com RRF simples
        scores = {}
        entries = {}
        
        for i, entry in enumerate(vector_results):
            scores[entry.id] = scores.get(entry.id, 0) + alpha / (i + 1)
            entries[entry.id] = entry
        
        for i, entry in enumerate(text_results):
            scores[entry.id] = scores.get(entry.id, 0) + (1 - alpha) / (i + 1)
            entries[entry.id] = entry
        
        # Ordena por score combinado
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        return [
            (entries[id], scores[id])
            for id in sorted_ids[:limit]
        ]
    
    # =========================================================================
    # MANAGEMENT OPERATIONS
    # =========================================================================
    
    async def delete_by_conversation(self, conversation_id: str) -> int:
        """Deleta todas as entradas de uma conversa."""
        await self._ensure_initialized()
        conn = self._get_connection()
        
        result = conn.execute(
            "DELETE FROM memory_entries WHERE conversation_id = ?",
            [conversation_id]
        )
        return result.rowcount
    
    async def delete_by_document(self, document_id: str) -> int:
        """Deleta embedding de um documento."""
        await self._ensure_initialized()
        conn = self._get_connection()
        
        result = conn.execute(
            "DELETE FROM document_embeddings WHERE document_id = ?",
            [document_id]
        )
        return result.rowcount
    
    async def count_entries(self, tenant_id: Optional[str] = None) -> int:
        """Conta entradas indexadas."""
        await self._ensure_initialized()
        conn = self._get_connection()
        
        result = conn.execute("SELECT COUNT(*) FROM memory_entries").fetchone()
        return result[0] if result else 0
    
    async def get_index_stats(self) -> dict:
        """Retorna estatísticas do índice."""
        await self._ensure_initialized()
        conn = self._get_connection()
        
        mem_count = conn.execute("SELECT COUNT(*) FROM memory_entries").fetchone()[0]
        doc_count = conn.execute("SELECT COUNT(*) FROM document_embeddings").fetchone()[0]
        
        return {
            "total_memory_entries": mem_count,
            "total_document_embeddings": doc_count,
            "dimension": self.dimension,
            "db_path": str(self.db_path),
        }
