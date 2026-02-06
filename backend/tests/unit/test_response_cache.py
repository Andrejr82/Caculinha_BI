# backend/tests/unit/test_response_cache.py

import pytest
import os
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.core.utils.response_cache import ResponseCache
from app.config.settings import Settings

@pytest.fixture
def temp_cache_dir(tmp_path):
    # Use pytest's tmp_path fixture to create a temporary directory
    cache_dir = tmp_path / "test_response_cache"
    cache_dir.mkdir()
    return cache_dir

@pytest.fixture
def mock_settings():
    # Mock settings to control CACHE_TTL_MINUTES
    mock_settings_instance = MagicMock(spec=Settings)
    mock_settings_instance.CACHE_TTL_MINUTES = 1 # 1 minute for testing
    with patch('backend.app.core.utils.response_cache.settings', mock_settings_instance):
        yield mock_settings_instance

def test_response_cache_init(temp_cache_dir, mock_settings):
    cache = ResponseCache(cache_dir=str(temp_cache_dir))
    assert os.path.exists(temp_cache_dir)
    assert cache.ttl == timedelta(minutes=1)

def test_generate_key(temp_cache_dir, mock_settings):
    cache = ResponseCache(cache_dir=str(temp_cache_dir))
    query = "test query"
    key = cache.generate_key(query)
    assert isinstance(key, str)
    assert len(key) == 64 # SHA256 hash length

def test_normalize_query(temp_cache_dir, mock_settings):
    cache = ResponseCache(cache_dir=str(temp_cache_dir))
    assert cache._normalize_query("Qual é o total de vendas?") == "total vendas"
    assert cache._normalize_query("  Query with   extra spaces !  ") == "query extra spaces"
    assert cache._normalize_query("Um teste, com. pontuação?") == "teste pontuação"

def test_set_and_get_cache_hit(temp_cache_dir, mock_settings):
    cache = ResponseCache(cache_dir=str(temp_cache_dir))
    query = "test query for cache hit"
    response_data = {"data": "some data", "status": "success"}
    key = cache.generate_key(query)
    
    cache.set(key, response_data)
    retrieved_data = cache.get(key)
    
    assert retrieved_data == response_data

def test_set_and_get_cache_miss_expired(temp_cache_dir, mock_settings):
    cache = ResponseCache(cache_dir=str(temp_cache_dir), ttl_minutes=0.01) # Very short TTL for testing
    query = "test query for cache miss"
    response_data = {"data": "some data", "status": "success"}
    key = cache.generate_key(query)
    
    cache.set(key, response_data)
    
    # Simulate time passing
    import time
    time.sleep(0.7) # Wait longer than 0.01 minutes
    
    retrieved_data = cache.get(key)
    assert retrieved_data is None
    assert not os.path.exists(cache._get_cache_file_path(key)) # Should have been cleaned

def test_cache_miss_file_not_found(temp_cache_dir, mock_settings):
    cache = ResponseCache(cache_dir=str(temp_cache_dir))
    key = "non_existent_key"
    retrieved_data = cache.get(key)
    assert retrieved_data is None

def test_cache_miss_corrupt_file(temp_cache_dir, mock_settings):
    cache = ResponseCache(cache_dir=str(temp_cache_dir))
    key = "corrupt_key"
    file_path = cache._get_cache_file_path(key)
    
    with open(file_path, "w") as f:
        f.write("invalid json")
    
    retrieved_data = cache.get(key)
    assert retrieved_data is None
    assert not os.path.exists(file_path) # Corrupt file should be removed

def test_clean_expired_cache(temp_cache_dir, mock_settings):
    cache = ResponseCache(cache_dir=str(temp_cache_dir), ttl_minutes=0.01)
    query_expired = "query to expire"
    query_valid = "query to remain valid"
    
    key_expired = cache.generate_key(query_expired)
    key_valid = cache.generate_key(query_valid)
    
    cache.set(key_expired, {"data": "expired"})
    
    # Simulate time passing for expired entry
    import time
    time.sleep(0.7)
    
    cache.set(key_valid, {"data": "valid"})
    
    cache.clean_expired_cache()
    
    assert cache.get(key_expired) is None
    assert cache.get(key_valid) is not None
