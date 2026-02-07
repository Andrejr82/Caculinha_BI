"""
MemoryEntry Entity — Entrada de Memória Vetorial

Representa uma entrada indexada para busca semântica.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4


@dataclass
class MemoryEntry:
    """
    Entidade de Entrada de Memória.
    
    Attributes:
        id: Identificador único (mem-uuid)
        conversation_id: FK para conversa
        message_id: FK para mensagem original
        content: Texto indexado
        embedding: Vetor de embeddings (768-dim)
        score: Score de relevância (0-1)
        metadata: Dados adicionais
    """
    
    conversation_id: str
    content: str
    id: str = field(default_factory=lambda: f"mem-{uuid4().hex[:12]}")
    message_id: Optional[str] = None
    embedding: Optional[List[float]] = None
    score: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validação pós-inicialização."""
        if not self.conversation_id:
            raise ValueError("conversation_id é obrigatório")
        if not self.content:
            raise ValueError("content é obrigatório")
    
    @property
    def has_embedding(self) -> bool:
        """Verifica se possui embedding."""
        return self.embedding is not None and len(self.embedding) > 0
    
    @property
    def embedding_dimension(self) -> int:
        """Retorna dimensão do embedding."""
        return len(self.embedding) if self.embedding else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário (sem embedding para economia)."""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "message_id": self.message_id,
            "content": self.content,
            "score": self.score,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }
    
    def to_dict_with_embedding(self) -> Dict[str, Any]:
        """Converte para dicionário incluindo embedding."""
        data = self.to_dict()
        data["embedding"] = self.embedding
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Cria instância a partir de dicionário."""
        return cls(
            id=data.get("id", f"mem-{uuid4().hex[:12]}"),
            conversation_id=data["conversation_id"],
            message_id=data.get("message_id"),
            content=data["content"],
            embedding=data.get("embedding"),
            score=data.get("score", 0.0),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            metadata=data.get("metadata"),
        )
    
    @classmethod
    def from_message(cls, message: Any, embedding: Optional[List[float]] = None) -> "MemoryEntry":
        """Cria MemoryEntry a partir de uma Message."""
        return cls(
            conversation_id=message.conversation_id,
            message_id=message.id,
            content=message.content,
            embedding=embedding,
        )
