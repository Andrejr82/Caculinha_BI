"""
Value Object: UserId

Identificador imutável de usuário.

Uso:
    from backend.domain.value_objects import UserId
    
    user_id = UserId("user-123")

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class UserId:
    """
    Value Object imutável para identificação de usuário.
    
    Attributes:
        value: O valor do identificador
    
    Example:
        >>> user_id = UserId("550e8400-e29b-41d4-a716-446655440000")
        >>> user_id.is_uuid
        True
    """
    
    value: str
    
    def __post_init__(self) -> None:
        """Valida o user_id no momento da criação."""
        if not self.value:
            raise ValueError("UserId não pode ser vazio")
        if len(self.value) > 100:
            raise ValueError("UserId não pode ter mais de 100 caracteres")
    
    @property
    def is_uuid(self) -> bool:
        """Verifica se o user_id é um UUID válido."""
        try:
            UUID(self.value)
            return True
        except (ValueError, AttributeError):
            return False
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"UserId('{self.value}')"
