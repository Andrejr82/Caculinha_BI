"""
Agent Graph Cache
Manages caching of agent graphs, both in-memory and on disk, with versioning.
"""

import time
import json
import os
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.config.settings import settings

class AgentGraphCache:
    """
    A hybrid in-memory and on-disk cache specifically for agent graphs.
    Supports versioning for automatic invalidation and TTL.
    (T6.1.1 from TASK_LIST)
    """

    def __init__(self, cache_dir: str = "data/cache_agent_graph", ttl_minutes: int = settings.AGENT_GRAPH_CACHE_TTL_MINUTES):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.ttl = timedelta(minutes=ttl_minutes)
        self.in_memory_cache: Dict[str, Dict[str, Any]] = {} # {key: {value: graph_data, timestamp: datetime, version: str}}
        print(f"AgentGraphCache initialized in {self.cache_dir} with TTL {self.ttl}")

        # Load existing cache from disk on startup
        self._load_all_from_disk()

    def _get_cache_file_path(self, key: str) -> str:
        """Generates a file path for a given cache key."""
        return os.path.join(self.cache_dir, f"{key}.json")

    def _get_current_version(self) -> str:
        """
        Generates a hash representing the current version of the agent's code/config.
        This hash is used to invalidate the cache if agent logic changes.
        (T6.1.4 from TASK_LIST)
        """
        # For simplicity, let's hash a combination of settings and a dummy version string.
        # In a real scenario, this would involve hashing agent source code files,
        # prompt templates, and relevant configuration files.
        version_data = {
            "agent_code_version": "1.0", # Placeholder: could be hash of agent source code
            "settings_llm_model": settings.LLM_MODEL_NAME,
            "settings_rag_model": settings.RAG_EMBEDDING_MODEL,
        }
        return hashlib.sha256(json.dumps(version_data, sort_keys=True).encode("utf-8")).hexdigest()

    def _load_from_disk(self, key: str) -> Optional[Dict[str, Any]]:
        """Loads a single cache entry from disk."""
        file_path = self._get_cache_file_path(key)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                return cached_data
            except (json.JSONDecodeError, OSError) as e:
                print(f"Error reading or decoding cache file {file_path}: {e}")
                if os.path.exists(file_path):
                    os.remove(file_path) # Remove corrupt file
        return None

    def _save_to_disk(self, key: str, value: Any, timestamp: datetime, version: str):
        """Saves a single cache entry to disk."""
        file_path = self._get_cache_file_path(key)
        data_to_cache = {
            "value": value,
            "timestamp": timestamp.isoformat(),
            "version": version
        }
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data_to_cache, f, ensure_ascii=False, indent=4)
            # print(f"Agent graph cache saved to disk for key: {key}")
        except OSError as e:
            print(f"Error writing agent graph cache file {file_path}: {e}")

    def _load_all_from_disk(self):
        """Loads all valid cache entries from disk into memory on startup."""
        current_version = self._get_current_version()
        for filename in os.listdir(self.cache_dir):
            if filename.endswith(".json"):
                key = filename[:-5] # Remove .json extension
                cached_data = self._load_from_disk(key)
                if cached_data:
                    cached_time = datetime.fromisoformat(cached_data["timestamp"])
                    if (datetime.now() - cached_time < self.ttl) and \
                       (cached_data.get("version") == current_version):
                        self.in_memory_cache[key] = cached_data
                        # print(f"Loaded valid agent graph cache for key: {key} from disk.")
                    else:
                        print(f"Invalidated old agent graph cache for key: {key} (expired or version mismatch).")
                        os.remove(self._get_cache_file_path(key))
    
    def get(self, key: str) -> Any:
        """
        Gets an entry from the cache (memory first, then disk).
        Checks for expiration and version compatibility.
        """
        current_version = self._get_current_version()
        
        # Check in-memory cache
        if key in self.in_memory_cache:
            entry = self.in_memory_cache[key]
            cached_time = datetime.fromisoformat(entry["timestamp"])
            if (datetime.now() - cached_time < self.ttl) and \
               (entry.get("version") == current_version):
                # print(f"Agent graph cache hit (in-memory) for key: {key}")
                return entry["value"]
            else:
                del self.in_memory_cache[key] # Expired or old version
        
        # Check disk cache if not found in memory or invalidated
        cached_data_from_disk = self._load_from_disk(key)
        if cached_data_from_disk:
            cached_time = datetime.fromisoformat(cached_data_from_disk["timestamp"])
            if (datetime.now() - cached_time < self.ttl) and \
               (cached_data_from_disk.get("version") == current_version):
                self.in_memory_cache[key] = cached_data_from_disk # Load into memory
                # print(f"Agent graph cache hit (disk) for key: {key}")
                return cached_data_from_disk["value"]
            else:
                print(f"Invalidated old agent graph cache for key: {key} (expired or version mismatch).")
                os.remove(self._get_cache_file_path(key))
        
        return None

    def set(self, key: str, value: Any) -> None:
        """
        Sets an entry in the cache (both in-memory and on disk).
        """
        timestamp = datetime.now()
        version = self._get_current_version()
        entry = {
            "value": value,
            "timestamp": timestamp.isoformat(),
            "version": version
        }
        self.in_memory_cache[key] = entry
        self._save_to_disk(key, value, timestamp, version)
        # print(f"Agent graph cache set for key: {key}")

    def clear(self, key: Optional[str] = None):
        """Clears a specific key or the entire cache."""
        if key:
            if key in self.in_memory_cache:
                del self.in_memory_cache[key]
            file_path = self._get_cache_file_path(key)
            if os.path.exists(file_path):
                os.remove(file_path)
            print(f"Agent graph cache cleared for key: {key}")
        else:
            self.in_memory_cache.clear()
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            print("All agent graph cache cleared.")

# Example usage
if __name__ == '__main__':
    # Ensure cache directory exists for testing
    os.makedirs(settings.LEARNING_EXAMPLES_PATH, exist_ok=True) # Using LEARNING_EXAMPLES_PATH as temp dir
    
    cache = AgentGraphCache(cache_dir=settings.LEARNING_EXAMPLES_PATH, ttl_minutes=1) # 1 minute TTL for testing

    test_key = "my_agent_graph_key"
    test_graph_data = {"nodes": ["A", "B"], "edges": [("A", "B")]}

    # Test set
    cache.set(test_key, test_graph_data)
    
    # Test get (should hit)
    retrieved = cache.get(test_key)
    print(f"Retrieved (should hit): {retrieved}")
    assert retrieved == test_graph_data

    # Test get (after expiration - manual simulation)
    print("Waiting for cache to expire (1 minute)...")
    import time
    time.sleep(65) # Wait a bit more than 1 minute

    retrieved_expired = cache.get(test_key)
    print(f"Retrieved (should miss after expiration): {retrieved_expired}")
    assert retrieved_expired is None

    # Test clear
    cache.set(test_key, test_graph_data)
    cache.clear(test_key)
    assert cache.get(test_key) is None

    print("\nAgentGraphCache tests passed!")

