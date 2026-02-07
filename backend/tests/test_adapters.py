"""
Testes de Adapters — Verificação de Infraestrutura

Autor: Testing Agent
Data: 2026-02-07
"""

import pytest
import tempfile
import os

from backend.infrastructure.adapters.sqlite_memory_adapter import SQLiteMemoryAdapter
from backend.infrastructure.adapters.duckdb_vector_adapter import DuckDBVectorAdapter
from backend.infrastructure.adapters.bm25_ranking_adapter import BM25RankingAdapter
from backend.infrastructure.adapters.duckdb_feature_store_adapter import DuckDBFeatureStoreAdapter
from backend.domain.entities.conversation import Conversation
from backend.domain.entities.message import Message
from backend.domain.entities.document import Document
from backend.domain.entities.embedding import Embedding
from backend.domain.entities.feature import Feature


class TestSQLiteMemoryAdapter:
    """Testes do SQLiteMemoryAdapter."""
    
    @pytest.fixture
    def adapter(self, tmp_path):
        db_path = str(tmp_path / "test_memory.db")
        return SQLiteMemoryAdapter(db_path)
    
    @pytest.mark.asyncio
    async def test_save_and_get_conversation(self, adapter):
        conv = Conversation(tenant_id="test", user_id="user1", title="Test")
        await adapter.save_conversation(conv)
        
        retrieved = await adapter.get_conversation(conv.id)
        assert retrieved is not None
        assert retrieved.title == "Test"
    
    @pytest.mark.asyncio
    async def test_add_and_get_messages(self, adapter):
        conv = Conversation(tenant_id="test", user_id="user1")
        await adapter.save_conversation(conv)
        
        msg = Message.user(conv.id, "Hello!")
        await adapter.add_message(msg)
        
        messages = await adapter.get_recent_messages(conv.id, limit=10)
        assert len(messages) >= 1
    
    @pytest.mark.asyncio
    async def test_delete_conversation(self, adapter):
        conv = Conversation(tenant_id="test", user_id="user1")
        await adapter.save_conversation(conv)
        
        deleted = await adapter.delete_conversation(conv.id)
        assert deleted
        
        retrieved = await adapter.get_conversation(conv.id)
        assert retrieved is None


class TestDuckDBVectorAdapter:
    """Testes do DuckDBVectorAdapter."""
    
    @pytest.fixture
    def adapter(self, tmp_path):
        db_path = str(tmp_path / "test_vectors.duckdb")
        return DuckDBVectorAdapter(db_path)
    
    @pytest.mark.asyncio
    async def test_index_and_search(self, adapter):
        doc = Document(tenant_id="test", content="Test document")
        embedding = Embedding(document_id=doc.id, vector=[0.1] * 768, model="test")
        
        await adapter.index_document(doc, embedding)
        
        results = await adapter.search_similar([0.1] * 768, limit=5, tenant_id="test")
        assert len(results) >= 1
    
    @pytest.mark.asyncio
    async def test_search_by_content(self, adapter):
        doc = Document(tenant_id="test", content="Unique content ABC123")
        embedding = Embedding(document_id=doc.id, vector=[0.5] * 768, model="test")
        await adapter.index_document(doc, embedding)
        
        results = await adapter.search_by_content("ABC123", limit=5, tenant_id="test")
        assert any("ABC123" in r.content for r in results)


class TestBM25RankingAdapter:
    """Testes do BM25RankingAdapter."""
    
    @pytest.fixture
    def adapter(self):
        return BM25RankingAdapter()
    
    @pytest.mark.asyncio
    async def test_rank_bm25(self, adapter):
        docs = [
            Document(tenant_id="test", content="Python programming language"),
            Document(tenant_id="test", content="Java programming language"),
            Document(tenant_id="test", content="Unrelated content"),
        ]
        
        ranked = await adapter.rank_bm25("Python programming", docs, top_k=3)
        
        assert len(ranked) == 3
        # Python doc should rank higher
        assert "Python" in ranked[0].document.content
    
    @pytest.mark.asyncio
    async def test_rrf(self, adapter):
        docs = [
            Document(tenant_id="test", content="Doc A"),
            Document(tenant_id="test", content="Doc B"),
        ]
        
        ranking1 = await adapter.rank_bm25("Doc A", docs)
        ranking2 = await adapter.rank_bm25("Doc B", docs)
        
        fused = await adapter.reciprocal_rank_fusion([ranking1, ranking2], top_k=2)
        assert len(fused) == 2


class TestDuckDBFeatureStoreAdapter:
    """Testes do DuckDBFeatureStoreAdapter."""
    
    @pytest.fixture
    def adapter(self, tmp_path):
        db_path = str(tmp_path / "test_features.duckdb")
        return DuckDBFeatureStoreAdapter(db_path)
    
    @pytest.mark.asyncio
    async def test_store_and_get_feature(self, adapter):
        feature = Feature(
            tenant_id="test",
            entity_id="product-123",
            feature_name="avg_sales",
            value=150.5,
        )
        
        await adapter.store_feature(feature)
        
        retrieved = await adapter.get_feature("test", "product-123", "avg_sales")
        assert retrieved is not None
        assert retrieved.value == 150.5
    
    @pytest.mark.asyncio
    async def test_get_features_for_entity(self, adapter):
        f1 = Feature(tenant_id="test", entity_id="entity-1", feature_name="feat_a", value=1)
        f2 = Feature(tenant_id="test", entity_id="entity-1", feature_name="feat_b", value=2)
        
        await adapter.store_feature(f1)
        await adapter.store_feature(f2)
        
        features = await adapter.get_features_for_entity("test", "entity-1")
        assert len(features) == 2
    
    @pytest.mark.asyncio
    async def test_list_feature_names(self, adapter):
        await adapter.store_feature(Feature(
            tenant_id="test", entity_id="e1", feature_name="unique_feature", value=1
        ))
        
        names = await adapter.list_feature_names("test")
        assert "unique_feature" in names
