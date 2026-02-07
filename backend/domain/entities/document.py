"""
Document Entity — Entidade de Documento

Representa um documento ingerido para RAG.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, Literal
from uuid import uuid4


DocumentSource = Literal["parquet", "csv", "pdf", "manual", "api"]


@dataclass
class Document:
    """
    Entidade de Documento.
    
    Attributes:
        id: Identificador único (doc-uuid)
        tenant_id: ID do tenant para isolamento
        content: Conteúdo textual do documento
        source: Origem do documento
        chunk_index: Índice do chunk (para documentos divididos)
        total_chunks: Total de chunks do documento original
        metadata: Dados adicionais (filename, etc)
    """
    
    tenant_id: str
    content: str
    source: DocumentSource = "manual"
    id: str = field(default_factory=lambda: f"doc-{uuid4().hex[:12]}")
    chunk_index: int = 0
    total_chunks: int = 1
    parent_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validação pós-inicialização."""
        if not self.tenant_id:
            raise ValueError("tenant_id é obrigatório")
        if not self.content:
            raise ValueError("content é obrigatório")
    
    @property
    def is_chunk(self) -> bool:
        """Verifica se é um chunk de documento maior."""
        return self.total_chunks > 1
    
    @property
    def token_estimate(self) -> int:
        """Estimativa de tokens (~4 chars por token)."""
        return len(self.content) // 4
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "content": self.content,
            "source": self.source,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "parent_id": self.parent_id,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Cria instância a partir de dicionário."""
        return cls(
            id=data.get("id", f"doc-{uuid4().hex[:12]}"),
            tenant_id=data["tenant_id"],
            content=data["content"],
            source=data.get("source", "manual"),
            chunk_index=data.get("chunk_index", 0),
            total_chunks=data.get("total_chunks", 1),
            parent_id=data.get("parent_id"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            metadata=data.get("metadata"),
        )
    
    @classmethod
    def create_chunks(
        cls, 
        tenant_id: str, 
        content: str, 
        chunk_size: int = 512,
        source: DocumentSource = "manual",
        metadata: Optional[Dict[str, Any]] = None
    ) -> list["Document"]:
        """
        Divide conteúdo em chunks.
        
        Args:
            tenant_id: ID do tenant
            content: Conteúdo completo
            chunk_size: Tamanho máximo por chunk (tokens)
            source: Origem do documento
            metadata: Metadados compartilhados
        
        Returns:
            Lista de Documents (chunks)
        """
        # Aproximação: 4 chars = 1 token
        char_size = chunk_size * 4
        chunks = []
        parent_id = f"doc-{uuid4().hex[:12]}"
        
        # Divide por parágrafos primeiro
        paragraphs = content.split("\n\n")
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < char_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Se não dividiu, força divisão por caracteres
        if len(chunks) == 0:
            chunks = [content[i:i+char_size] for i in range(0, len(content), char_size)]
        
        return [
            cls(
                tenant_id=tenant_id,
                content=chunk,
                source=source,
                chunk_index=i,
                total_chunks=len(chunks),
                parent_id=parent_id if len(chunks) > 1 else None,
                metadata=metadata,
            )
            for i, chunk in enumerate(chunks)
        ]
