# backend/app/core/utils/response_cache.py

import json
import os
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from backend.app.config.settings import settings
from backend.app.infrastructure.redis_client import get_sync_redis_client
import re

logger = logging.getLogger(__name__)

class ResponseCache:
    """
    Manages caching of LLM responses on disk with a configurable TTL.
    Normalizes queries for better cache hit rates.
    """
    def __init__(self, cache_dir: str = "data/cache", ttl_minutes: int = settings.CACHE_TTL_MINUTES):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.ttl = timedelta(minutes=ttl_minutes)
        self.ttl_seconds = max(1, int(self.ttl.total_seconds()))
        logger.info("ResponseCache initialized in %s with TTL %s", self.cache_dir, self.ttl)

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
        redis_client = get_sync_redis_client()
        if redis_client is not None:
            try:
                cached_payload = redis_client.get(self._redis_key(key))
                if cached_payload:
                    return json.loads(cached_payload)
            except Exception as exc:
                logger.warning("Redis cache read failed for key %s: %s", key, exc)

        file_path = self._get_cache_file_path(key)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                
                cached_time_str = cached_data.get("timestamp")
                if cached_time_str:
                    cached_time = datetime.fromisoformat(cached_time_str)
                    if datetime.now() - cached_time < self.ttl:
                        logger.debug("Cache hit for key %s", key)
                        return cached_data.get("response")
                    else:
                        logger.info("Cache expired for key %s. Deleting...", key)
                        os.remove(file_path) # Clean up expired cache
                else:
                    logger.warning("Cache data for key %s missing timestamp. Deleting...", key)
                    os.remove(file_path) # Invalid cache entry
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Error reading or decoding cache file %s: %s. Deleting...", file_path, e)
                if os.path.exists(file_path):
                    os.remove(file_path)
        return None

    def set(self, key: str, response: Dict[str, Any]):
        """
        Stores a response in the cache with a timestamp.
        """
        redis_client = get_sync_redis_client()
        if redis_client is not None:
            try:
                redis_client.setex(self._redis_key(key), self.ttl_seconds, json.dumps(response, ensure_ascii=False))
            except Exception as exc:
                logger.warning("Redis cache write failed for key %s: %s", key, exc)

        file_path = self._get_cache_file_path(key)
        data_to_cache = {
            "timestamp": datetime.now().isoformat(),
            "response": response
        }
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data_to_cache, f, ensure_ascii=False, indent=4)
            logger.debug("Cache set for key %s", key)
        except OSError as e:
            logger.warning("Error writing cache file %s: %s", file_path, e)

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
                            logger.info("Cleaned expired cache file %s", filename)
                    else:
                        os.remove(file_path)
                        logger.info("Cleaned invalid cache file (no timestamp): %s", filename)
                except (json.JSONDecodeError, OSError) as e:
                    logger.warning("Error checking/cleaning cache file %s: %s. Removing.", file_path, e)
                    if os.path.exists(file_path):
                        os.remove(file_path)

    def _redis_key(self, key: str) -> str:
        return f"{settings.REDIS_KEY_PREFIX}:response_cache:{key}"

