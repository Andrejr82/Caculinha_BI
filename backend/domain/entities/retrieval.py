"""
Retrieval Entities — Entidades de Busca e Ranqueamento

Define as estruturas de dados retornadas pelo motor de busca híbrida.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from backend.domain.entities.product_canonical import ProductCanonical


@dataclass
class RankingScores:
    """Detalhamento dos scores de ranqueamento."""
    bm25: float = 0.0
    vector: float = 0.0
    rules: float = 0.0
    final: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bm25": self.bm25,
            "vector": self.vector,
            "rules": self.rules,
            "final": self.final
        }


@dataclass
class RetrievedItem:
    """Item recuperado de um índice (pré-fusão)."""
    product_id: int
    score: float
    source: str  # 'bm25' or 'vector'
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RankedProduct:
    """Produto final após fusão e rerank."""
    product: ProductCanonical
    scores: RankingScores
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product": self.product.to_dict(),
            "scores": self.scores.to_dict(),
            "rationale": self.rationale
        }
