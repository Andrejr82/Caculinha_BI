import json

import pytest

from backend.app.api.middleware.rate_limit import RateLimitMiddleware
from backend.app.core.utils.response_cache import ResponseCache
from backend.app.core.utils.semantic_cache import SemanticCache


class FakeSyncRedis:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, ttl, value):
        self.store[key] = value

    def ping(self):
        return True

    def close(self):
        return None


class FakeAsyncRedis:
    def __init__(self):
        self.zsets = {}
        self.expirations = {}

    async def zremrangebyscore(self, key, min_score, max_score):
        items = self.zsets.get(key, [])
        self.zsets[key] = [(member, score) for member, score in items if score > max_score]

    async def zcard(self, key):
        return len(self.zsets.get(key, []))

    async def zadd(self, key, mapping):
        bucket = self.zsets.setdefault(key, [])
        for member, score in mapping.items():
            bucket.append((member, score))

    async def expire(self, key, window_seconds):
        self.expirations[key] = window_seconds


def test_response_cache_prefers_redis(monkeypatch, tmp_path):
    redis_client = FakeSyncRedis()
    monkeypatch.setattr(
        "backend.app.core.utils.response_cache.get_sync_redis_client",
        lambda: redis_client,
    )

    cache = ResponseCache(cache_dir=str(tmp_path / "cache"), ttl_minutes=1)
    key = cache.generate_key("consulta redis")
    payload = {"status": "success", "value": 123}
    cache.set(key, payload)

    redis_key = cache._redis_key(key)
    assert json.loads(redis_client.store[redis_key]) == payload
    assert cache.get(key) == payload


def test_semantic_cache_reads_exact_hit_from_redis(monkeypatch, tmp_path):
    redis_client = FakeSyncRedis()
    monkeypatch.setattr(
        "backend.app.core.utils.semantic_cache.get_sync_redis_client",
        lambda: redis_client,
    )

    cache = SemanticCache(cache_dir=str(tmp_path / "semantic"), ttl_minutes=1)
    payload = {"answer": "ok"}
    query = "vendas produto 369947"
    cache.set(query, payload, user_id="u1")

    key = cache._generate_key(query, "u1")
    redis_key = cache._redis_response_key(key)
    assert json.loads(redis_client.store[redis_key]) == payload
    assert cache.get(query, user_id="u1") == payload


def test_semantic_cache_does_not_fuzzy_match_different_segment_filters(monkeypatch, tmp_path):
    redis_client = FakeSyncRedis()
    monkeypatch.setattr(
        "backend.app.core.utils.semantic_cache.get_sync_redis_client",
        lambda: redis_client,
    )

    cache = SemanticCache(cache_dir=str(tmp_path / "semantic"), ttl_minutes=1)
    cache.set(
        "gere um gráfico com a venda do segmento informatica em cada loja",
        {"answer": "informatica"},
        user_id="u1",
    )

    assert (
        cache.get(
            "gere um gráfico com a venda do segmento papelaria em cada loja",
            user_id="u1",
        )
        is None
    )


def test_semantic_cache_does_not_fuzzy_match_different_store_filters(monkeypatch, tmp_path):
    redis_client = FakeSyncRedis()
    monkeypatch.setattr(
        "backend.app.core.utils.semantic_cache.get_sync_redis_client",
        lambda: redis_client,
    )

    cache = SemanticCache(cache_dir=str(tmp_path / "semantic"), ttl_minutes=1)
    cache.set(
        "qual o total de vendas da loja 520 no segmento tecidos",
        {"answer": "loja 520"},
        user_id="u1",
    )

    assert (
        cache.get(
            "qual o total de vendas da loja 1685 no segmento tecidos",
            user_id="u1",
        )
        is None
    )


@pytest.mark.asyncio
async def test_rate_limit_middleware_uses_redis_window(monkeypatch):
    redis_client = FakeAsyncRedis()
    monkeypatch.setattr(
        "backend.app.api.middleware.rate_limit.get_redis_client",
        lambda: redis_client,
    )

    middleware = RateLimitMiddleware(app=lambda scope, receive, send: None)

    first = await middleware._check_rate_limit("tenant:user", 2, 60)
    second = await middleware._check_rate_limit("tenant:user", 2, 60)
    third = await middleware._check_rate_limit("tenant:user", 2, 60)

    assert first[0] is True
    assert second[0] is True
    assert third[0] is False
