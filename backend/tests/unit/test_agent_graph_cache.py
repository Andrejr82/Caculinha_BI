# backend/tests/unit/test_agent_graph_cache.py

import pytest
import os
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.core.cache import AgentGraphCache
from app.config.settings import Settings

@pytest.fixture
def temp_agent_graph_cache_dir(tmp_path):
    cache_dir = tmp_path / "test_agent_graph_cache"
    cache_dir.mkdir()
    return cache_dir

@pytest.fixture
def mock_settings():
    mock_settings_instance = MagicMock(spec=Settings)
    mock_settings_instance.AGENT_GRAPH_CACHE_TTL_MINUTES = 1 # 1 minute for testing
    mock_settings_instance.LLM_MODEL_NAME = "test_llm_model"
    mock_settings_instance.RAG_EMBEDDING_MODEL = "test_rag_model"
    with patch('backend.app.core.cache.settings', mock_settings_instance):
        yield mock_settings_instance

def test_agent_graph_cache_init(temp_agent_graph_cache_dir, mock_settings):
    cache = AgentGraphCache(cache_dir=str(temp_agent_graph_cache_dir))
    assert os.path.exists(temp_agent_graph_cache_dir)
    assert cache.ttl == timedelta(minutes=1)
    assert cache.in_memory_cache == {} # Should be empty initially as no files were loaded

def test_get_current_version(temp_agent_graph_cache_dir, mock_settings):
    cache = AgentGraphCache(cache_dir=str(temp_agent_graph_cache_dir))
    version = cache._get_current_version()
    assert isinstance(version, str)
    assert len(version) == 64 # SHA256 hash length

def test_set_and_get_cache_hit(temp_agent_graph_cache_dir, mock_settings):
    cache = AgentGraphCache(cache_dir=str(temp_agent_graph_cache_dir))
    key = "test_graph_key"
    graph_data = {"nodes": ["A", "B"], "edges": [("A", "B")]}
    
    cache.set(key, graph_data)
    retrieved_data = cache.get(key)
    
    assert retrieved_data == graph_data
    assert key in cache.in_memory_cache
    assert os.path.exists(cache._get_cache_file_path(key))

def test_get_cache_miss_expired(temp_agent_graph_cache_dir, mock_settings):
    cache = AgentGraphCache(cache_dir=str(temp_agent_graph_cache_dir), ttl_minutes=0.01) # Very short TTL
    key = "expired_graph_key"
    graph_data = {"nodes": ["X", "Y"]}
    
    cache.set(key, graph_data)
    
    import time
    time.sleep(0.7) # Wait longer than 0.01 minutes
    
    retrieved_data = cache.get(key)
    assert retrieved_data is None
    assert key not in cache.in_memory_cache
    assert not os.path.exists(cache._get_cache_file_path(key)) # Should have been cleaned

def test_get_cache_miss_version_mismatch(temp_agent_graph_cache_dir):
    mock_settings_v1 = MagicMock(spec=Settings)
    mock_settings_v1.AGENT_GRAPH_CACHE_TTL_MINUTES = 60
    mock_settings_v1.LLM_MODEL_NAME = "v1_llm"
    mock_settings_v1.RAG_EMBEDDING_MODEL = "v1_rag"

    mock_settings_v2 = MagicMock(spec=Settings)
    mock_settings_v2.AGENT_GRAPH_CACHE_TTL_MINUTES = 60
    mock_settings_v2.LLM_MODEL_NAME = "v2_llm" # Changed version
    mock_settings_v2.RAG_EMBEDDING_MODEL = "v1_rag"

    key = "version_mismatch_key"
    graph_data = {"nodes": ["V1", "Graph"]}

    # Create cache with V1 settings
    with patch('backend.app.core.cache.settings', mock_settings_v1):
        cache_v1 = AgentGraphCache(cache_dir=str(temp_agent_graph_cache_dir))
        cache_v1.set(key, graph_data)
        assert cache_v1.get(key) == graph_data

    # Now try to retrieve with V2 settings
    with patch('backend.app.core.cache.settings', mock_settings_v2):
        cache_v2 = AgentGraphCache(cache_dir=str(temp_agent_graph_cache_dir))
        retrieved_data = cache_v2.get(key)
        assert retrieved_data is None # Should miss due to version mismatch
        assert key not in cache_v2.in_memory_cache
        assert not os.path.exists(cache_v2._get_cache_file_path(key)) # Old version should be removed

def test_clear_specific_key(temp_agent_graph_cache_dir, mock_settings):
    cache = AgentGraphCache(cache_dir=str(temp_agent_graph_cache_dir))
    key1 = "graph_key_1"
    key2 = "graph_key_2"
    cache.set(key1, {"data": 1})
    cache.set(key2, {"data": 2})

    cache.clear(key1)
    assert cache.get(key1) is None
    assert cache.get(key2) == {"data": 2}
    assert not os.path.exists(cache._get_cache_file_path(key1))
    assert os.path.exists(cache._get_cache_file_path(key2))

def test_clear_all(temp_agent_graph_cache_dir, mock_settings):
    cache = AgentGraphCache(cache_dir=str(temp_agent_graph_cache_dir))
    key1 = "graph_key_1"
    key2 = "graph_key_2"
    cache.set(key1, {"data": 1})
    cache.set(key2, {"data": 2})

    cache.clear()
    assert cache.get(key1) is None
    assert cache.get(key2) is None
    assert not os.listdir(temp_agent_graph_cache_dir) # Directory should be empty

def test_corrupt_file_handling(temp_agent_graph_cache_dir, mock_settings):
    cache = AgentGraphCache(cache_dir=str(temp_agent_graph_cache_dir))
    key = "corrupt_file_key"
    file_path = cache._get_cache_file_path(key)
    with open(file_path, "w") as f:
        f.write("{invalid json") # Write corrupt JSON

    retrieved = cache.get(key)
    assert retrieved is None
    assert not os.path.exists(file_path) # Corrupt file should be deleted
