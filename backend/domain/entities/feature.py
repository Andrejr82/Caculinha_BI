"""
Feature Entity — Entidade de Feature

Representa uma feature para Feature Store (ML).

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, Union, List
from uuid import uuid4


FeatureValue = Union[float, int, str, bool, List[float]]


@dataclass
class Feature:
    """
    Entidade de Feature para Feature Store.
    
    Attributes:
        id: Identificador único (feat-uuid)
        tenant_id: ID do tenant para isolamento
        entity_id: ID da entidade (produto, loja, etc)
        feature_name: Nome da feature
        value: Valor da feature
        version: Versão da feature (para versionamento)
        ttl_seconds: Tempo de vida em segundos (0 = permanente)
    """
    
    tenant_id: str
    entity_id: str
    feature_name: str
    value: FeatureValue
    id: str = field(default_factory=lambda: f"feat-{uuid4().hex[:12]}")
    version: int = 1
    ttl_seconds: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validação pós-inicialização."""
        if not self.tenant_id:
            raise ValueError("tenant_id é obrigatório")
        if not self.entity_id:
            raise ValueError("entity_id é obrigatório")
        if not self.feature_name:
            raise ValueError("feature_name é obrigatório")
    
    @property
    def feature_key(self) -> str:
        """Chave única da feature (tenant:entity:name)."""
        return f"{self.tenant_id}:{self.entity_id}:{self.feature_name}"
    
    @property
    def is_expired(self) -> bool:
        """Verifica se feature expirou."""
        if self.ttl_seconds == 0:
            return False
        elapsed = (datetime.utcnow() - self.created_at).total_seconds()
        return elapsed > self.ttl_seconds
    
    @property
    def value_type(self) -> str:
        """Retorna tipo do valor."""
        if isinstance(self.value, bool):
            return "bool"
        if isinstance(self.value, int):
            return "int"
        if isinstance(self.value, float):
            return "float"
        if isinstance(self.value, str):
            return "str"
        if isinstance(self.value, list):
            return "vector"
        return "unknown"
    
    def update_value(self, new_value: FeatureValue) -> None:
        """Atualiza valor e incrementa versão."""
        self.value = new_value
        self.version += 1
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "entity_id": self.entity_id,
            "feature_name": self.feature_name,
            "value": self.value,
            "value_type": self.value_type,
            "version": self.version,
            "ttl_seconds": self.ttl_seconds,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Feature":
        """Cria instância a partir de dicionário."""
        return cls(
            id=data.get("id", f"feat-{uuid4().hex[:12]}"),
            tenant_id=data["tenant_id"],
            entity_id=data["entity_id"],
            feature_name=data["feature_name"],
            value=data["value"],
            version=data.get("version", 1),
            ttl_seconds=data.get("ttl_seconds", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.utcnow(),
            metadata=data.get("metadata"),
        )
