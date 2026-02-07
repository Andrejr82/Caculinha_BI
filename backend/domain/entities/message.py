"""
Message Entity — Entidade de Mensagem

Representa uma mensagem individual em uma conversa.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, Literal
from uuid import uuid4


MessageRole = Literal["user", "assistant", "system", "tool"]


@dataclass
class Message:
    """
    Entidade de Mensagem.
    
    Attributes:
        id: Identificador único (msg-uuid)
        conversation_id: FK para conversa
        role: Papel (user, assistant, system, tool)
        content: Conteúdo da mensagem
        timestamp: Momento da criação
        metadata: Dados adicionais (tool_calls, etc)
    """
    
    conversation_id: str
    role: MessageRole
    content: str
    id: str = field(default_factory=lambda: f"msg-{uuid4().hex[:12]}")
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validação pós-inicialização."""
        if not self.conversation_id:
            raise ValueError("conversation_id é obrigatório")
        if self.role not in ("user", "assistant", "system", "tool"):
            raise ValueError(f"role inválido: {self.role}")
    
    @property
    def token_estimate(self) -> int:
        """Estimativa de tokens (~4 chars por token)."""
        return len(self.content) // 4
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
    
    def to_llm_format(self) -> Dict[str, str]:
        """Formato para LLM (role + content)."""
        return {"role": self.role, "content": self.content}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Cria instância a partir de dicionário."""
        return cls(
            id=data.get("id", f"msg-{uuid4().hex[:12]}"),
            conversation_id=data["conversation_id"],
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
            metadata=data.get("metadata"),
        )
    
    @classmethod
    def user(cls, conversation_id: str, content: str) -> "Message":
        """Factory para mensagem de usuário."""
        return cls(conversation_id=conversation_id, role="user", content=content)
    
    @classmethod
    def assistant(cls, conversation_id: str, content: str) -> "Message":
        """Factory para mensagem de assistente."""
        return cls(conversation_id=conversation_id, role="assistant", content=content)
    
    @classmethod
    def system(cls, conversation_id: str, content: str) -> "Message":
        """Factory para mensagem de sistema."""
        return cls(conversation_id=conversation_id, role="system", content=content)
