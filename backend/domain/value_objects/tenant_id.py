"""
Value Object: TenantId

Identificador imutável de tenant para multi-tenancy.

Uso:
    from backend.domain.value_objects import TenantId
    
    tenant_id = TenantId("lojas-cacula")
    tenant_id.validate()

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class TenantId:
    """
    Value Object imutável para identificação de tenant.
    
    Attributes:
        value: O valor do identificador
    
    Example:
        >>> tenant_id = TenantId("lojas-cacula")
        >>> tenant_id.value
        'lojas-cacula'
        >>> tenant_id.is_valid()
        True
    """
    
    value: str
    
    def __post_init__(self) -> None:
        """Valida o tenant_id no momento da criação."""
        if not self.value:
            raise ValueError("TenantId não pode ser vazio")
        if len(self.value) > 100:
            raise ValueError("TenantId não pode ter mais de 100 caracteres")
    
    def is_valid(self) -> bool:
        """Verifica se o tenant_id é válido."""
        pattern = r'^[a-z0-9][a-z0-9\-_]{0,98}[a-z0-9]$|^[a-z0-9]$'
        return bool(re.match(pattern, self.value))
    
    def validate(self) -> None:
        """Valida o formato do tenant_id, levantando exceção se inválido."""
        if not self.is_valid():
            raise ValueError(
                f"TenantId inválido: '{self.value}'. "
                "Deve conter apenas letras minúsculas, números, hífens e underscores."
            )
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"TenantId('{self.value}')"
