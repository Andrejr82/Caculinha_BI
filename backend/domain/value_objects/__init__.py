"""
Domain Value Objects - Inicialização

Este módulo contém os value objects imutáveis do domínio.

Uso:
    from backend.domain.value_objects import TenantId, UserId, TimeRange

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from backend.domain.value_objects.tenant_id import TenantId
from backend.domain.value_objects.user_id import UserId
from backend.domain.value_objects.message_id import MessageId
from backend.domain.value_objects.time_range import TimeRange

__all__ = [
    "TenantId",
    "UserId",
    "MessageId",
    "TimeRange",
]
