"""
IFeatureStore Port — Interface de Feature Store

Define contrato para armazenamento e recuperação de features ML.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from backend.domain.entities.feature import Feature, FeatureValue


class IFeatureStore(ABC):
    """
    Interface para Feature Store.
    
    Responsabilidades:
    - CRUD de features
    - Lookup por entidade
    - Versionamento e TTL
    """
    
    # =========================================================================
    # FEATURE OPERATIONS
    # =========================================================================
    
    @abstractmethod
    async def store_feature(self, feature: Feature) -> str:
        """
        Armazena uma feature.
        
        Args:
            feature: Feature a armazenar
        
        Returns:
            ID da feature armazenada
        """
        pass
    
    @abstractmethod
    async def get_feature(
        self,
        tenant_id: str,
        entity_id: str,
        feature_name: str,
        version: Optional[int] = None,
    ) -> Optional[Feature]:
        """
        Recupera uma feature.
        
        Args:
            tenant_id: ID do tenant
            entity_id: ID da entidade
            feature_name: Nome da feature
            version: Versão específica (None = última)
        
        Returns:
            Feature ou None se não encontrada
        """
        pass
    
    @abstractmethod
    async def get_features_for_entity(
        self,
        tenant_id: str,
        entity_id: str,
        feature_names: Optional[List[str]] = None,
    ) -> Dict[str, Feature]:
        """
        Recupera todas as features de uma entidade.
        
        Args:
            tenant_id: ID do tenant
            entity_id: ID da entidade
            feature_names: Filtrar por nomes (None = todas)
        
        Returns:
            Dict de feature_name -> Feature
        """
        pass
    
    @abstractmethod
    async def update_feature(
        self,
        tenant_id: str,
        entity_id: str,
        feature_name: str,
        value: FeatureValue,
    ) -> bool:
        """
        Atualiza valor de uma feature.
        
        Args:
            tenant_id: ID do tenant
            entity_id: ID da entidade
            feature_name: Nome da feature
            value: Novo valor
        
        Returns:
            True se atualizada, False se não encontrada
        """
        pass
    
    @abstractmethod
    async def delete_feature(
        self,
        tenant_id: str,
        entity_id: str,
        feature_name: str,
    ) -> bool:
        """
        Deleta uma feature.
        
        Args:
            tenant_id: ID do tenant
            entity_id: ID da entidade
            feature_name: Nome da feature
        
        Returns:
            True se deletada
        """
        pass
    
    # =========================================================================
    # BATCH OPERATIONS
    # =========================================================================
    
    @abstractmethod
    async def batch_store(self, features: List[Feature]) -> List[str]:
        """
        Armazena múltiplas features em lote.
        
        Args:
            features: Lista de features
        
        Returns:
            Lista de IDs armazenados
        """
        pass
    
    @abstractmethod
    async def batch_get(
        self,
        tenant_id: str,
        entity_ids: List[str],
        feature_names: List[str],
    ) -> Dict[str, Dict[str, Feature]]:
        """
        Recupera features para múltiplas entidades.
        
        Args:
            tenant_id: ID do tenant
            entity_ids: Lista de IDs de entidades
            feature_names: Lista de nomes de features
        
        Returns:
            Dict de entity_id -> {feature_name -> Feature}
        """
        pass
    
    # =========================================================================
    # METADATA OPERATIONS
    # =========================================================================
    
    @abstractmethod
    async def list_feature_names(
        self,
        tenant_id: str,
    ) -> List[str]:
        """
        Lista nomes de features disponíveis.
        
        Args:
            tenant_id: ID do tenant
        
        Returns:
            Lista de nomes únicos
        """
        pass
    
    @abstractmethod
    async def get_feature_stats(
        self,
        tenant_id: str,
        feature_name: str,
    ) -> Dict[str, Any]:
        """
        Retorna estatísticas de uma feature.
        
        Args:
            tenant_id: ID do tenant
            feature_name: Nome da feature
        
        Returns:
            Dict com count, min, max, avg, etc.
        """
        pass
    
    @abstractmethod
    async def cleanup_expired(self, tenant_id: Optional[str] = None) -> int:
        """
        Remove features expiradas.
        
        Args:
            tenant_id: Filtrar por tenant (None = todos)
        
        Returns:
            Número de features removidas
        """
        pass
