"""
Product Catalog Ports — Interfaces de Catálogo de Produtos

Define os contratos para extração, normalização, gestão de sinônimos e versionamento do catálogo.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.domain.entities.product_canonical import ProductCanonical
from backend.domain.entities.synonym import SynonymEntry, CanonicalTerm
from backend.domain.entities.taxonomy import TaxonomyNode


class IProductSourcePort(ABC):
    """Porta para extração de dados brutos da fonte original (Parquet)."""
    
    @abstractmethod
    async def load_full_catalog(self) -> List[Dict[str, Any]]:
        """Carrega todos os produtos da fonte admmat.parquet."""
        pass
    
    @abstractmethod
    async def load_incremental_catalog(self, since: datetime) -> List[Dict[str, Any]]:
        """Carrega produtos alterados desde uma data específica."""
        pass


class IProductCatalogRepository(ABC):
    """Porta para persistência do catálogo derivado e versionado."""
    
    @abstractmethod
    async def save_products(self, products: List[ProductCanonical], version: str) -> bool:
        """Salva uma lista de produtos associada a uma versão."""
        pass
    
    @abstractmethod
    async def get_product(self, product_id: int, version: str) -> Optional[ProductCanonical]:
        """Recupera um produto específico de uma versão do catálogo."""
        pass
    
    @abstractmethod
    async def list_products(self, version: str, limit: int = 100, offset: int = 0) -> List[ProductCanonical]:
        """Lista produtos de uma versão específica."""
        pass


class ISynonymRepository(ABC):
    """Porta para gestão de sinônimos e termos canônicos."""
    
    @abstractmethod
    async def save_synonyms(self, synonyms: List[CanonicalTerm]) -> bool:
        """Salva/atualiza dicionário de sinônimos."""
        pass
    
    @abstractmethod
    async def get_synonyms_for_term(self, term: str) -> List[str]:
        """Busca sinônimos associados a um termo."""
        pass


class INormalizationPort(ABC):
    """Porta para normalização de texto pt-BR e mapeamento canônico."""
    
    @abstractmethod
    def normalize_text(self, text: str) -> str:
        """Limpa texto, remove acentos, lower case, etc."""
        pass

    @abstractmethod
    def normalize_series(self, series: "pd.Series") -> "pd.Series":
        """Normalização vetorizada para Pandas Series."""
        pass
    
    @abstractmethod
    def tokenize(self, text: str) -> List[str]:
        """Divide texto em tokens significativos."""
        pass


class ICatalogVersionPort(ABC):
    """Porta para gestão de versões e ciclo de vida do catálogo."""
    
    @abstractmethod
    async def create_version(self, description: str) -> str:
        """Cria uma nova entrada de versão e retorna o catalog_version (uuid/id)."""
        pass
    
    @abstractmethod
    async def activate_version(self, version: str) -> bool:
        """Define uma versão como a ativa para buscas."""
        pass
    
    @abstractmethod
    async def get_active_version(self) -> Optional[str]:
        """Retorna o ID da versão ativa no momento."""
        pass
    
    @abstractmethod
    async def rollback_to_previous(self) -> Optional[str]:
        """Reverte para a versão estável imediatamente anterior."""
        pass
