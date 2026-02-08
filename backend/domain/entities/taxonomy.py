"""
Taxonomy Entity — Entidades de Taxonomia

Define a estrutura de departamentos e categorias.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class TaxonomyNode:
    """Nó na árvore de taxonomia (Departamento, Categoria ou Subcategoria)."""
    name: str
    level: str  # 'dept', 'category', 'subcategory'
    parent_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "level": self.level,
            "parent_name": self.parent_name,
            "metadata": self.metadata
        }
