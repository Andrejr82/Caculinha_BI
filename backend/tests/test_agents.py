"""
Testes de Agentes — Verificação de Funcionalidade

Autor: Testing Agent
Data: 2026-02-07
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.application.agents.base_agent import AgentRequest, AgentResponse
from backend.application.agents.memory_agent import MemoryAgent
from backend.application.agents.vectorization_agent import VectorizationAgent
from backend.application.agents.rag_agent import RAGAgent
from backend.application.agents.sql_agent import SQLAgent
from backend.application.agents.insight_agent import InsightAgent
from backend.application.agents.orchestrator_agent import OrchestratorAgent


class TestMemoryAgent:
    """Testes do MemoryAgent."""
    
    @pytest.fixture
    def mock_memory_repo(self):
        repo = AsyncMock()
        repo.save_conversation = AsyncMock(return_value="conv-123")
        repo.get_recent_messages = AsyncMock(return_value=[])
        repo.get_conversation = AsyncMock(return_value=None)
        return repo
    
    @pytest.fixture
    def memory_agent(self, mock_memory_repo):
        return MemoryAgent(mock_memory_repo)
    
    @pytest.mark.asyncio
    async def test_create_conversation(self, memory_agent):
        conv = await memory_agent.create_conversation(
            tenant_id="tenant-test",
            user_id="user-test",
            title="Conversa de teste",
        )
        
        assert conv.id.startswith("conv-")
        assert conv.tenant_id == "tenant-test"
        assert conv.title == "Conversa de teste"
    
    @pytest.mark.asyncio
    async def test_load_memory_empty(self, memory_agent):
        messages = await memory_agent.load_memory("conv-123")
        assert messages == []
    
    @pytest.mark.asyncio
    async def test_execute(self, memory_agent):
        request = AgentRequest(
            content="test",
            conversation_id="conv-123",
            tenant_id="test",
            user_id="user",
        )
        response = await memory_agent.run(request)
        assert response.success
        assert "Memória carregada" in response.content


class TestVectorizationAgent:
    """Testes do VectorizationAgent."""
    
    @pytest.fixture
    def vectorization_agent(self):
        return VectorizationAgent()
    
    @pytest.mark.asyncio
    async def test_embed_text_fallback(self, vectorization_agent):
        embedding = await vectorization_agent.embed_text("Hello world")
        assert embedding is not None
        assert len(embedding) == 768  # Default dimension
    
    @pytest.mark.asyncio
    async def test_embed_empty(self, vectorization_agent):
        embedding = await vectorization_agent.embed_text("")
        assert embedding is None
    
    @pytest.mark.asyncio
    async def test_embed_batch(self, vectorization_agent):
        embeddings = await vectorization_agent.embed_batch(["a", "b", "c"])
        assert len(embeddings) == 3


class TestRAGAgent:
    """Testes do RAGAgent."""
    
    @pytest.fixture
    def mock_vector_repo(self):
        repo = AsyncMock()
        repo.search_similar = AsyncMock(return_value=[])
        repo.search_by_content = AsyncMock(return_value=[])
        return repo
    
    @pytest.fixture
    def rag_agent(self, mock_vector_repo):
        return RAGAgent(mock_vector_repo)
    
    @pytest.mark.asyncio
    async def test_search_empty(self, rag_agent):
        results = await rag_agent.search("test query")
        assert results == []
    
    def test_format_context_empty(self, rag_agent):
        context = rag_agent._format_context([])
        assert context == ""
    
    def test_augment_prompt(self, rag_agent):
        augmented = rag_agent.augment_prompt("Question?", "Context here")
        assert "Context here" in augmented
        assert "Question?" in augmented


class TestSQLAgent:
    """Testes do SQLAgent."""
    
    @pytest.fixture
    def sql_agent(self, tmp_path):
        return SQLAgent(str(tmp_path / "test.duckdb"))
    
    @pytest.mark.asyncio
    async def test_query_simple(self, sql_agent):
        result = await sql_agent.query("SELECT 1 as num")
        assert len(result) == 1
        assert result[0]["num"] == 1
    
    @pytest.mark.asyncio
    async def test_query_error(self, sql_agent):
        result = await sql_agent.query("SELECT * FROM nonexistent")
        assert result == []


class TestInsightAgent:
    """Testes do InsightAgent."""
    
    @pytest.fixture
    def insight_agent(self):
        return InsightAgent()
    
    @pytest.mark.asyncio
    async def test_generate_basic_insight(self, insight_agent):
        insight = await insight_agent.generate_insight(
            "Como estão as vendas?",
            {"total_vendas": 1000, "produtos": ["A", "B"]}
        )
        assert "total_vendas" in insight or "vendas" in insight.lower()
    
    @pytest.mark.asyncio
    async def test_analyze_trend_insufficient(self, insight_agent):
        result = await insight_agent.analyze_trend([{"date": "2026-01-01"}], "date", "value")
        assert "insuficientes" in result.lower()


class TestOrchestratorAgent:
    """Testes do OrchestratorAgent."""
    
    @pytest.fixture
    def orchestrator(self):
        return OrchestratorAgent()
    
    @pytest.mark.asyncio
    async def test_execute_minimal(self, orchestrator):
        request = AgentRequest(
            content="Olá",
            conversation_id="conv-123",
            tenant_id="test",
            user_id="user",
        )
        response = await orchestrator.run(request)
        assert response.success
        assert response.agent_name == "OrchestratorAgent"
