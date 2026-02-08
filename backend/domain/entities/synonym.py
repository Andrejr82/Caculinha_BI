"""
Synonym Entity — Entidades de Sinônimos

Define mapeamentos entre termos de busca e termos canônicos.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class CanonicalTerm:
    """Termo canônico com seus sinônimos."""
    term: str
    synonyms: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"term": self.term, "synonyms": self.synonyms}


@dataclass
class SynonymEntry:
    """Entrada individual de sinônimo para mapeamento reverso."""
    term: str
    canonical_target: str

    def to_dict(self) -> Dict[str, Any]:
        return {"term": self.term, "canonical_target": self.canonical_target}
