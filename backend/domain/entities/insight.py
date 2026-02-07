"""
Entity: Insight

Define a entidade Insight que representa um insight gerado pelo sistema.

Uso:
    from backend.domain.entities import Insight, InsightLevel
    
    insight = Insight(
        title="Crescimento de Vendas",
        content="As vendas cresceram 15% este mês",
        level=InsightLevel.POSITIVE
    )

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import uuid4


class InsightLevel(str, Enum):
    """Níveis de criticidade do insight."""
    
    CRITICAL = "critical"    # Requer ação imediata
    WARNING = "warning"      # Atenção necessária
    POSITIVE = "positive"    # Boas notícias
    NEUTRAL = "neutral"      # Informativo


class InsightCategory(str, Enum):
    """Categorias de insights."""
    
    SALES = "sales"
    STOCK = "stock"
    RUPTURE = "rupture"
    TREND = "trend"
    ANOMALY = "anomaly"
    FORECAST = "forecast"


@dataclass
class Insight:
    """
    Entidade que representa um insight gerado pelo sistema.
    
    Attributes:
        id: Identificador único
        title: Título do insight
        content: Conteúdo/descrição do insight
        level: Nível de criticidade
        category: Categoria do insight
        data: Dados associados ao insight
        tenant_id: ID do tenant (multi-tenancy)
        created_at: Data de criação
    
    Example:
        >>> insight = Insight(
        ...     title="Ruptura Detectada",
        ...     content="Produto X está em ruptura na loja 1685",
        ...     level=InsightLevel.CRITICAL,
        ...     category=InsightCategory.RUPTURE
        ... )
        >>> insight.is_critical
        True
    """
    
    title: str
    content: str
    level: InsightLevel = InsightLevel.NEUTRAL
    category: Optional[InsightCategory] = None
    id: str = field(default_factory=lambda: str(uuid4()))
    data: Dict[str, Any] = field(default_factory=dict)
    tenant_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_critical(self) -> bool:
        """Verifica se o insight é crítico."""
        return self.level == InsightLevel.CRITICAL
    
    @property
    def is_actionable(self) -> bool:
        """Verifica se o insight requer ação."""
        return self.level in (InsightLevel.CRITICAL, InsightLevel.WARNING)
    
    def add_tag(self, tag: str) -> None:
        """Adiciona uma tag ao insight."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def set_data(self, key: str, value: Any) -> None:
        """Define um dado associado ao insight."""
        self.data[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o insight para dicionário."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "level": self.level.value,
            "category": self.category.value if self.category else None,
            "data": self.data,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
        }
    
    def __repr__(self) -> str:
        return f"Insight(title='{self.title[:30]}', level={self.level.value})"
