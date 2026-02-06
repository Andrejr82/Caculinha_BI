# backend/app/core/utils/response_cache.py

import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from app.config.settings import settings
import re

class ResponseCache:
    """
    Manages caching of LLM responses on disk with a configurable TTL.
    Normalizes queries for better cache hit rates.
    """
    def __init__(self, cache_dir: str = "data/cache", ttl_minutes: int = settings.CACHE_TTL_MINUTES):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.ttl = timedelta(minutes=ttl_minutes)
        print(f"ResponseCache initialized in {self.cache_dir} with TTL {self.ttl}")

    def _get_cache_file_path(self, key: str) -> str:
        """Generates a file path for a given cache key."""
        return os.path.join(self.cache_dir, f"{key}.json")

    def generate_key(self, query: str) -> str:
        """
        Generates a cache key by normalizing the query and hashing it.
        This ensures consistent keys for similar queries.
        """
        normalized_query = self._normalize_query(query)
        return hashlib.sha256(normalized_query.encode("utf-8")).hexdigest()

    def _normalize_query(self, query: str) -> str:
        """
        Normalizes a query string for caching purposes.
        Removes stopwords, standardizes spaces, lowercases, removes irrelevant punctuation.
        (T6.1.3 from TASK_LIST, but implemented here as it's directly related to cache key generation)
        """
        query_lower = query.lower()
        # Example stopwords (expand as needed)
        stopwords = ["o", "a", "os", "as", "um", "uma", "uns", "umas", "de", "da", "do", "dos", "das", "em", "no", "na", "nos", "nas", "que", "e", "é", "para", "com", "por"]
        words = [word for word in query_lower.split() if word not in stopwords]
        
        normalized = " ".join(words)
        normalized = re.sub(r'[^\w\s]', '', normalized) # Remove punctuation (keep alphanumeric and space)
        normalized = re.sub(r'\s+', ' ', normalized).strip() # Standardize spaces
        return normalized

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a cached response if it exists and is not expired.
        """
        file_path = self._get_cache_file_path(key)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                
                cached_time_str = cached_data.get("timestamp")
                if cached_time_str:
                    cached_time = datetime.fromisoformat(cached_time_str)
                    if datetime.now() - cached_time < self.ttl:
                        print(f"Cache hit for key: {key}")
                        return cached_data.get("response")
                    else:
                        print(f"Cache expired for key: {key}. Deleting...")
                        os.remove(file_path) # Clean up expired cache
                else:
                    print(f"Cache data for key: {key} missing timestamp. Deleting...")
                    os.remove(file_path) # Invalid cache entry
            except (json.JSONDecodeError, OSError) as e:
                print(f"Error reading or decoding cache file {file_path}: {e}. Deleting...")
                if os.path.exists(file_path):
                    os.remove(file_path)
        return None

    def set(self, key: str, response: Dict[str, Any]):
        """
        Stores a response in the cache with a timestamp.
        """
        file_path = self._get_cache_file_path(key)
        data_to_cache = {
            "timestamp": datetime.now().isoformat(),
            "response": response
        }
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data_to_cache, f, ensure_ascii=False, indent=4)
            print(f"Cache set for key: {key}")
        except OSError as e:
            print(f"Error writing cache file {file_path}: {e}")

    def clean_expired_cache(self):
        """
        Cleans up expired cache files (T1.3.1 - cache_cleaner).
        This method will be called by a separate cache cleaner utility in production,
        but can be manually triggered or run periodically.
        """
        for filename in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, filename)
            if filename.endswith(".json") and os.path.isfile(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        cached_data = json.load(f)
                    cached_time_str = cached_data.get("timestamp")
                    if cached_time_str:
                        cached_time = datetime.fromisoformat(cached_time_str)
                        if datetime.now() - cached_time >= self.ttl:
                            os.remove(file_path)
                            print(f"Cleaned expired cache file: {filename}")
                    else:
                        os.remove(file_path)
                        print(f"Cleaned invalid cache file (no timestamp): {filename}")
                except (json.JSONDecodeError, OSError) as e:
                    print(f"Error checking/cleaning cache file {file_path}: {e}. Removing.")
                    if os.path.exists(file_path):
                        os.remove(file_path)

# Example usage
if __name__ == '__main__':
    # Ensure cache directory exists for testing
    os.makedirs(settings.LEARNING_FEEDBACK_PATH, exist_ok=True) # Assuming LEARNING_FEEDBACK_PATH is a good temp dir
    cache = ResponseCache(cache_dir=settings.LEARNING_FEEDBACK_PATH, ttl_minutes=1) # 1 minute TTL for testing

    test_query = "Qual é o total de vendas por produto para o segmento A?"
    test_response = {"result": [{"product": "X", "sales": 100}], "chart_spec": None}

    key = cache.generate_key(test_query)
    print(f"\nGenerated key for '{test_query}': {key}")

    # Test set
    cache.set(key, test_response)
    
    # Test get (should hit)
    retrieved = cache.get(key)
    print(f"Retrieved (should hit): {retrieved}")
    assert retrieved == test_response

    # Test get (after expiration - manual simulation)
    print("Waiting for cache to expire (1 minute)...")
    import time
    time.sleep(65) # Wait a bit more than 1 minute

    retrieved_expired = cache.get(key)
    print(f"Retrieved (should miss after expiration): {retrieved_expired}")
    assert retrieved_expired is None

    # Test clean_expired_cache
    cache.set(key, test_response) # Set again to have something to expire
    time.sleep(65)
    print("\nRunning cache cleanup...")
    cache.clean_expired_cache()
    assert cache.get(key) is None # Should be gone after cleanup

    print("\nResponseCache tests passed!")
