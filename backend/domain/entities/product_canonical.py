"""
ProductCanonical Entity — Entidade de Produto Canônico

Representa a versão normalizada e enriquecida de um produto para busca.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass
class ProductCanonical:
    """
    Entidade de Produto Canônico.
    
    Attributes:
        product_id: ID original do produto
        name_raw: Nome original na base
        name_canonical: Nome normalizado e limpo
        brand: Marca do produto
        dept: Departamento/Segmento
        category: Categoria/Grupo
        subcategory: Subcategoria/Subgrupo
        attributes_json: Metadados adicionais em JSON
        status: Status do produto (ativo/inativo)
        updated_at: Timestamp de última atualização
        searchable_text: Texto consolidado para indexação
        tokens_normalized: Lista de tokens processados
        catalog_version: Versão do catálogo a que pertence
    """
    
    product_id: int
    name_raw: str
    name_canonical: str
    brand: str
    dept: str
    category: str
    subcategory: str
    catalog_version: str
    attributes_json: Dict[str, Any] = field(default_factory=dict)
    status: str = "active"
    updated_at: datetime = field(default_factory=datetime.utcnow)
    searchable_text: str = ""
    tokens_normalized: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "product_id": self.product_id,
            "name_raw": self.name_raw,
            "name_canonical": self.name_canonical,
            "brand": self.brand,
            "dept": self.dept,
            "category": self.category,
            "subcategory": self.subcategory,
            "attributes_json": self.attributes_json,
            "status": self.status,
            "updated_at": self.updated_at.isoformat(),
            "searchable_text": self.searchable_text,
            "tokens_normalized": self.tokens_normalized,
            "catalog_version": self.catalog_version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductCanonical":
        """Cria instância a partir de dicionário."""
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        elif updated_at is None:
            updated_at = datetime.utcnow()
            
        return cls(
            product_id=data["product_id"],
            name_raw=data["name_raw"],
            name_canonical=data["name_canonical"],
            brand=data.get("brand", ""),
            dept=data.get("dept", ""),
            category=data.get("category", ""),
            subcategory=data.get("subcategory", ""),
            catalog_version=data["catalog_version"],
            attributes_json=data.get("attributes_json", {}),
            status=data.get("status", "active"),
            updated_at=updated_at,
            searchable_text=data.get("searchable_text", ""),
            tokens_normalized=data.get("tokens_normalized", [])
        )
