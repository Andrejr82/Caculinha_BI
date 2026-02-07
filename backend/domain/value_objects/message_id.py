"""
Value Object: MessageId

Identificador imutável de mensagem.

Uso:
    from backend.domain.value_objects import MessageId
    
    msg_id = MessageId.generate()

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from dataclasses import dataclass
from uuid import uuid4, UUID


@dataclass(frozen=True)
class MessageId:
    """
    Value Object imutável para identificação de mensagem.
    
    Attributes:
        value: O valor do identificador (UUID string)
    
    Example:
        >>> msg_id = MessageId.generate()
        >>> msg_id.is_valid
        True
    """
    
    value: str
    
    def __post_init__(self) -> None:
        """Valida o message_id no momento da criação."""
        if not self.value:
            raise ValueError("MessageId não pode ser vazio")
    
    @classmethod
    def generate(cls) -> "MessageId":
        """Gera um novo MessageId único."""
        return cls(str(uuid4()))
    
    @property
    def is_valid(self) -> bool:
        """Verifica se o message_id é um UUID válido."""
        try:
            UUID(self.value)
            return True
        except (ValueError, AttributeError):
            return False
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"MessageId('{self.value}')"
