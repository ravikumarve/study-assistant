"""Tests for /api/progress endpoint."""

import pytest, json
from unittest.mock import patch


class TestProgressEndpoint:
    def test_get_progress_returns_correct_schema(self, client):
        # First create some progress data
        client.post(
            "/api/progress",
            json={"topic": "Python", "activity": "explanation", "score": None},
            headers={"X-Session-Token": "progress-test-1"},
        )

        # Then get progress
        resp = client.get(
            "/api/progress", headers={"X-Session-Token": "progress-test-1"}
        )
        data = resp.get_json()

        assert resp.status_code == 200
        assert data["success"] is True
        for field in ["stats", "recent_topics", "activity_breakdown", "streak_days"]:
            assert field in data["data"]

    def test_post_progress_success(self, client):
        resp = client.post(
            "/api/progress",
            json={"topic": "Python", "activity": "quiz", "score": 85.5},
            headers={"X-Session-Token": "progress-test-2"},
        )
        data = resp.get_json()

        assert resp.status_code == 200
        assert data["success"] is True
        assert data["data"]["saved"] is True

    def test_post_progress_missing_topic_returns_400(self, client):
        resp = client.post("/api/progress", json={"activity": "quiz", "score": 85.5})
        data = resp.get_json()
        assert resp.status_code == 400
        assert data["success"] is False
        assert data["code"] == "INVALID_INPUT"

    def test_post_progress_missing_activity_returns_400(self, client):
        resp = client.post("/api/progress", json={"topic": "Python", "score": 85.5})
        data = resp.get_json()
        assert resp.status_code == 400
        assert data["success"] is False
        assert data["code"] == "INVALID_INPUT"

    def test_post_progress_invalid_activity_returns_400(self, client):
        resp = client.post(
            "/api/progress",
            json={"topic": "Python", "activity": "invalid", "score": 85.5},
        )
        data = resp.get_json()
        assert resp.status_code == 400
        assert data["success"] is False
        assert data["code"] == "INVALID_INPUT"

    def test_progress_not_cached(self, client):
        # First request
        resp1 = client.get("/api/progress", headers={"X-Session-Token": "cache-test-1"})
        # Second request - should not be cached
        resp2 = client.get("/api/progress", headers={"X-Session-Token": "cache-test-1"})
        assert resp2.get_json()["cached"] is False  # Progress should never be cached

    def test_topic_exceeding_max_length_returns_400(self, client):
        resp = client.post(
            "/api/progress",
            json={"topic": "x" * 500, "activity": "quiz", "score": 85.5},
        )
        assert resp.status_code == 400

    def test_score_range_validation(self, client):
        # Test score too high
        resp = client.post(
            "/api/progress",
            json={"topic": "Python", "activity": "quiz", "score": 150.0},
        )
        assert resp.status_code == 400

        # Test score too low
        resp = client.post(
            "/api/progress",
            json={"topic": "Python", "activity": "quiz", "score": -10.0},
        )
        assert resp.status_code == 400

        # Test valid score
        resp = client.post(
            "/api/progress", json={"topic": "Python", "activity": "quiz", "score": 95.0}
        )
        assert resp.status_code == 200
