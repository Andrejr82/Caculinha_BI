"""
FeatureStoreAgent — Agente de Feature Store

Autor: Orchestrator Agent
Data: 2026-02-07
"""

from typing import List, Dict, Optional, Any
import structlog

from backend.application.agents.base_agent import BaseAgent, AgentRequest, AgentResponse
from backend.domain.ports.feature_store_port import IFeatureStore
from backend.domain.entities.feature import Feature, FeatureValue

logger = structlog.get_logger(__name__)


class FeatureStoreAgent(BaseAgent):
    """Agente responsável por gerenciar Feature Store."""
    
    def __init__(self, feature_store: IFeatureStore):
        super().__init__(
            name="FeatureStoreAgent",
            description="Gerencia features para ML",
            capabilities=["store", "get", "update", "batch_operations"]
        )
        self.store = feature_store
    
    async def _execute(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse(content="FeatureStore agent ready", agent_name=self.name)
    
    async def store_feature(
        self, tenant_id: str, entity_id: str, feature_name: str, value: FeatureValue, ttl: int = 0
    ) -> str:
        """Armazena uma feature."""
        feature = Feature(
            tenant_id=tenant_id, entity_id=entity_id,
            feature_name=feature_name, value=value, ttl_seconds=ttl
        )
        return await self.store.store_feature(feature)
    
    async def get_feature(
        self, tenant_id: str, entity_id: str, feature_name: str
    ) -> Optional[Feature]:
        """Recupera uma feature."""
        return await self.store.get_feature(tenant_id, entity_id, feature_name)
    
    async def get_entity_features(
        self, tenant_id: str, entity_id: str, names: Optional[List[str]] = None
    ) -> Dict[str, Feature]:
        """Recupera features de uma entidade."""
        return await self.store.get_features_for_entity(tenant_id, entity_id, names)
    
    async def batch_store(self, features: List[Feature]) -> List[str]:
        """Armazena features em lote."""
        return await self.store.batch_store(features)
    
    async def cleanup_expired(self, tenant_id: Optional[str] = None) -> int:
        """Remove features expiradas."""
        return await self.store.cleanup_expired(tenant_id)
