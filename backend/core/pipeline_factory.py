"""
Pipeline Factory — Fábrica do Pipeline Cognitivo

Autor: Orchestrator Agent
Data: 2026-02-07
"""

from typing import Optional
import structlog

# Domain
from backend.domain.ports.memory_repository_port import IMemoryRepository
from backend.domain.ports.vector_repository_port import IVectorRepository
from backend.domain.ports.ranking_port import IRankingPort
from backend.domain.ports.compression_port import ICompressionPort
from backend.domain.ports.feature_store_port import IFeatureStore

# Adapters
from backend.infrastructure.adapters.sqlite_memory_adapter import SQLiteMemoryAdapter
from backend.infrastructure.adapters.duckdb_vector_adapter import DuckDBVectorAdapter
from backend.infrastructure.adapters.bm25_ranking_adapter import BM25RankingAdapter
from backend.infrastructure.adapters.llm_compression_adapter import LLMCompressionAdapter
from backend.infrastructure.adapters.duckdb_feature_store_adapter import DuckDBFeatureStoreAdapter

# Agents
from backend.application.agents.orchestrator_agent import OrchestratorAgent
from backend.application.agents.memory_agent import MemoryAgent
from backend.application.agents.vectorization_agent import VectorizationAgent
from backend.application.agents.rag_agent import RAGAgent
from backend.application.agents.ranking_agent import RankingAgent
from backend.application.agents.compression_agent import CompressionAgent
from backend.application.agents.feature_store_agent import FeatureStoreAgent
from backend.application.agents.sql_agent import SQLAgent
from backend.application.agents.insight_agent import InsightAgent


logger = structlog.get_logger(__name__)


class PipelineFactory:
    """Fábrica para criação do pipeline cognitivo."""
    
    def __init__(
        self,
        data_dir: str = "data",
        llm_client=None,
        embedding_client=None,
    ):
        self.data_dir = data_dir
        self.llm_client = llm_client
        self.embedding_client = embedding_client
        
        # Adapters (lazy init)
        self._memory_adapter: Optional[IMemoryRepository] = None
        self._vector_adapter: Optional[IVectorRepository] = None
        self._ranking_adapter: Optional[IRankingPort] = None
        self._compression_adapter: Optional[ICompressionPort] = None
        self._feature_store_adapter: Optional[IFeatureStore] = None
        
        # Agents (lazy init)
        self._memory_agent: Optional[MemoryAgent] = None
        self._vectorization_agent: Optional[VectorizationAgent] = None
        self._rag_agent: Optional[RAGAgent] = None
        self._ranking_agent: Optional[RankingAgent] = None
        self._compression_agent: Optional[CompressionAgent] = None
        self._feature_store_agent: Optional[FeatureStoreAgent] = None
        self._sql_agent: Optional[SQLAgent] = None
        self._insight_agent: Optional[InsightAgent] = None
        self._orchestrator: Optional[OrchestratorAgent] = None
    
    # =========================================================================
    # ADAPTERS
    # =========================================================================
    
    def get_memory_adapter(self) -> IMemoryRepository:
        if self._memory_adapter is None:
            self._memory_adapter = SQLiteMemoryAdapter(f"{self.data_dir}/memory.db")
        return self._memory_adapter
    
    def get_vector_adapter(self) -> IVectorRepository:
        if self._vector_adapter is None:
            self._vector_adapter = DuckDBVectorAdapter(f"{self.data_dir}/vectors.duckdb")
        return self._vector_adapter
    
    def get_ranking_adapter(self) -> IRankingPort:
        if self._ranking_adapter is None:
            self._ranking_adapter = BM25RankingAdapter()
        return self._ranking_adapter
    
    def get_compression_adapter(self) -> ICompressionPort:
        if self._compression_adapter is None:
            self._compression_adapter = LLMCompressionAdapter(llm_client=self.llm_client)
        return self._compression_adapter
    
    def get_feature_store_adapter(self) -> IFeatureStore:
        if self._feature_store_adapter is None:
            self._feature_store_adapter = DuckDBFeatureStoreAdapter(f"{self.data_dir}/features.duckdb")
        return self._feature_store_adapter
    
    # =========================================================================
    # AGENTS
    # =========================================================================
    
    def get_memory_agent(self) -> MemoryAgent:
        if self._memory_agent is None:
            self._memory_agent = MemoryAgent(self.get_memory_adapter())
        return self._memory_agent
    
    def get_vectorization_agent(self) -> VectorizationAgent:
        if self._vectorization_agent is None:
            self._vectorization_agent = VectorizationAgent(embedding_client=self.embedding_client)
        return self._vectorization_agent
    
    def get_rag_agent(self) -> RAGAgent:
        if self._rag_agent is None:
            self._rag_agent = RAGAgent(
                self.get_vector_adapter(),
                self.get_vectorization_agent()
            )
        return self._rag_agent
    
    def get_ranking_agent(self) -> RankingAgent:
        if self._ranking_agent is None:
            self._ranking_agent = RankingAgent(self.get_ranking_adapter())
        return self._ranking_agent
    
    def get_compression_agent(self) -> CompressionAgent:
        if self._compression_agent is None:
            self._compression_agent = CompressionAgent(self.get_compression_adapter())
        return self._compression_agent
    
    def get_feature_store_agent(self) -> FeatureStoreAgent:
        if self._feature_store_agent is None:
            self._feature_store_agent = FeatureStoreAgent(self.get_feature_store_adapter())
        return self._feature_store_agent
    
    def get_sql_agent(self) -> SQLAgent:
        if self._sql_agent is None:
            self._sql_agent = SQLAgent(f"{self.data_dir}/analytics.duckdb")
        return self._sql_agent
    
    def get_insight_agent(self) -> InsightAgent:
        if self._insight_agent is None:
            self._insight_agent = InsightAgent(llm_client=self.llm_client)
        return self._insight_agent
    
    # =========================================================================
    # ORCHESTRATOR
    # =========================================================================
    
    def get_orchestrator(self) -> OrchestratorAgent:
        """Retorna orchestrator completo com todos os agentes."""
        if self._orchestrator is None:
            self._orchestrator = OrchestratorAgent(
                memory_agent=self.get_memory_agent(),
                vectorization_agent=self.get_vectorization_agent(),
                rag_agent=self.get_rag_agent(),
                ranking_agent=self.get_ranking_agent(),
                compression_agent=self.get_compression_agent(),
                sql_agent=self.get_sql_agent(),
                insight_agent=self.get_insight_agent(),
                llm_client=self.llm_client,
            )
            logger.info("orchestrator_created", agents=9)
        return self._orchestrator
    
    def create_minimal_orchestrator(self) -> OrchestratorAgent:
        """Cria orchestrator mínimo (sem todas as dependências)."""
        return OrchestratorAgent(
            memory_agent=self.get_memory_agent(),
            insight_agent=self.get_insight_agent(),
            llm_client=self.llm_client,
        )


# Singleton global
_factory: Optional[PipelineFactory] = None


def get_pipeline_factory() -> PipelineFactory:
    """Retorna factory singleton."""
    global _factory
    if _factory is None:
        _factory = PipelineFactory()
    return _factory


def configure_pipeline(
    data_dir: str = "data",
    llm_client=None,
    embedding_client=None,
) -> PipelineFactory:
    """Configura e retorna factory."""
    global _factory
    _factory = PipelineFactory(
        data_dir=data_dir,
        llm_client=llm_client,
        embedding_client=embedding_client,
    )
    return _factory
