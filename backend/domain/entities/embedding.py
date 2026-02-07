"""
Embedding Entity — Entidade de Embedding

Representa um vetor de embedding para busca semântica.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4


@dataclass
class Embedding:
    """
    Entidade de Embedding.
    
    Attributes:
        id: Identificador único (emb-uuid)
        document_id: FK para documento
        vector: Vetor de embedding (768-dim padrão)
        model: Modelo usado para gerar embedding
        dimension: Dimensão do vetor
    """
    
    document_id: str
    vector: List[float]
    model: str = "gemini-embedding-001"
    id: str = field(default_factory=lambda: f"emb-{uuid4().hex[:12]}")
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validação pós-inicialização."""
        if not self.document_id:
            raise ValueError("document_id é obrigatório")
        if not self.vector or len(self.vector) == 0:
            raise ValueError("vector não pode ser vazio")
    
    @property
    def dimension(self) -> int:
        """Retorna dimensão do vetor."""
        return len(self.vector)
    
    @property
    def is_normalized(self) -> bool:
        """Verifica se vetor está normalizado (L2 norm ≈ 1)."""
        import math
        norm = math.sqrt(sum(x*x for x in self.vector))
        return abs(norm - 1.0) < 0.01
    
    def normalize(self) -> "Embedding":
        """Retorna cópia normalizada do embedding."""
        import math
        norm = math.sqrt(sum(x*x for x in self.vector))
        if norm == 0:
            return self
        normalized_vector = [x / norm for x in self.vector]
        return Embedding(
            id=self.id,
            document_id=self.document_id,
            vector=normalized_vector,
            model=self.model,
            created_at=self.created_at,
            metadata=self.metadata,
        )
    
    def cosine_similarity(self, other: "Embedding") -> float:
        """Calcula similaridade de cosseno com outro embedding."""
        if self.dimension != other.dimension:
            raise ValueError(f"Dimensões incompatíveis: {self.dimension} vs {other.dimension}")
        
        dot_product = sum(a * b for a, b in zip(self.vector, other.vector))
        
        import math
        norm_a = math.sqrt(sum(x*x for x in self.vector))
        norm_b = math.sqrt(sum(x*x for x in other.vector))
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário (sem vetor para economia)."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "model": self.model,
            "dimension": self.dimension,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }
    
    def to_dict_with_vector(self) -> Dict[str, Any]:
        """Converte para dicionário incluindo vetor."""
        data = self.to_dict()
        data["vector"] = self.vector
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Embedding":
        """Cria instância a partir de dicionário."""
        return cls(
            id=data.get("id", f"emb-{uuid4().hex[:12]}"),
            document_id=data["document_id"],
            vector=data["vector"],
            model=data.get("model", "gemini-embedding-001"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            metadata=data.get("metadata"),
        )
