"""
Conversation Entity — Entidade de Conversa

Representa uma conversa entre usuário e sistema.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4


@dataclass
class Conversation:
    """
    Entidade de Conversa.
    
    Attributes:
        id: Identificador único (conv-uuid)
        tenant_id: ID do tenant para isolamento
        user_id: ID do usuário proprietário
        title: Título da conversa (auto-gerado)
        created_at: Timestamp de criação
        updated_at: Timestamp de última atualização
        metadata: Dados adicionais opcionais
    """
    
    tenant_id: str
    user_id: str
    id: str = field(default_factory=lambda: f"conv-{uuid4().hex[:12]}")
    title: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validação pós-inicialização."""
        if not self.tenant_id:
            raise ValueError("tenant_id é obrigatório")
        if not self.user_id:
            raise ValueError("user_id é obrigatório")
    
    def update_timestamp(self) -> None:
        """Atualiza o timestamp de modificação."""
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """Cria instância a partir de dicionário."""
        return cls(
            id=data.get("id", f"conv-{uuid4().hex[:12]}"),
            tenant_id=data["tenant_id"],
            user_id=data["user_id"],
            title=data.get("title"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.utcnow(),
            metadata=data.get("metadata"),
        )
