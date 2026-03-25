"""Tests for cache system."""

import pytest, json
from datetime import datetime, timedelta
from unittest.mock import patch


class TestCacheSystem:
    def test_cache_get_set(self, client):
        # Test cache set and get
        from app import cache_set, cache_get, make_cache_key

        key = make_cache_key("test", {"param": "value"})
        value = {"test": "data"}

        cache_set(key, value)
        cached = cache_get(key)

        assert cached == value

    def test_cache_expiration(self, client):
        from app import cache_set, cache_get, make_cache_key

        key = make_cache_key("test", {"param": "value"})
        value = {"test": "data"}

        # Set with very short TTL
        cache_set(key, value, ttl_hours=0.001)  # 3.6 seconds

        # Should still be available
        cached = cache_get(key)
        assert cached == value

        # Mock time to test expiration
        with patch("app.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime.utcnow() + timedelta(hours=1)
            cached = cache_get(key)
            assert cached is None

    def test_cache_key_stability(self, client):
        from app import make_cache_key

        # Same parameters should generate same key regardless of order
        key1 = make_cache_key("test", {"a": 1, "b": 2, "c": 3})
        key2 = make_cache_key("test", {"c": 3, "b": 2, "a": 1})

        assert key1 == key2

    def test_cache_miss_returns_none(self, client):
        from app import cache_get

        cached = cache_get("nonexistent_key")
        assert cached is None

    def test_cache_overwrite(self, client):
        from app import cache_set, cache_get, make_cache_key

        key = make_cache_key("test", {"param": "value"})
        value1 = {"test": "data1"}
        value2 = {"test": "data2"}

        cache_set(key, value1)
        cache_set(key, value2)  # Overwrite
        cached = cache_get(key)

        assert cached == value2

    def test_endpoint_caching(self, client, mock_ollama):
        mock_ollama.return_value = json.dumps(
            {
                "explanation": "test",
                "examples": [],
                "key_concepts": [],
                "analogies": [],
                "misconceptions": [],
            }
        )

        payload = {"topic": "CacheTest", "level": "beginner"}

        # First request - cache miss
        resp1 = client.post(
            "/api/explain", json=payload, headers={"X-Session-Token": "cache-test-1"}
        )
        assert resp1.get_json()["cached"] is False

        # Second request - cache hit
        resp2 = client.post(
            "/api/explain", json=payload, headers={"X-Session-Token": "cache-test-1"}
        )
        assert resp2.get_json()["cached"] is True

    def test_different_params_different_cache(self, client, mock_ollama):
        mock_ollama.return_value = json.dumps(
            {
                "explanation": "test",
                "examples": [],
                "key_concepts": [],
                "analogies": [],
                "misconceptions": [],
            }
        )

        # Request 1
        resp1 = client.post(
            "/api/explain",
            json={"topic": "Python", "level": "beginner"},
            headers={"X-Session-Token": "cache-test-2"},
        )

        # Request 2 - different level
        resp2 = client.post(
            "/api/explain",
            json={"topic": "Python", "level": "advanced"},
            headers={"X-Session-Token": "cache-test-2"},
        )

        # Both should be cache misses
        assert resp1.get_json()["cached"] is False
        assert resp2.get_json()["cached"] is False

    def test_chat_not_cached(self, client, mock_ollama):
        mock_ollama.return_value = json.dumps({"response": "test", "suggestions": []})

        payload = {"message": "Hello", "history": []}

        # First request
        resp1 = client.post(
            "/api/chat", json=payload, headers={"X-Session-Token": "cache-test-3"}
        )

        # Second request - should not be cached
        resp2 = client.post(
            "/api/chat", json=payload, headers={"X-Session-Token": "cache-test-3"}
        )

        assert resp2.get_json()["cached"] is False  # Chat should never be cached
