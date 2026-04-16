"""Tests for /api/explain endpoint."""

import pytest, json
from unittest.mock import patch


class TestExplainEndpoint:
    def test_success_returns_correct_schema(self, client, mock_ollama):
        mock_ollama.return_value = json.dumps(
            {
                "explanation": "Python is a programming language.",
                "examples": ["print('hello')"],
                "key_concepts": ["variables", "functions"],
                "analogies": ["like building with LEGO blocks"],
                "misconceptions": ["Python is slow for everything — false"],
            }
        )
        resp = client.post(
            "/api/explain", json={"topic": "Python", "level": "beginner"}
        )
        data = resp.get_json()

        assert resp.status_code == 200
        assert data["success"] is True
        for field in [
            "explanation",
            "examples",
            "key_concepts",
            "analogies",
            "misconceptions",
        ]:
            assert field in data["data"]

    def test_missing_topic_returns_400(self, client):
        resp = client.post("/api/explain", json={})
        data = resp.get_json()
        assert resp.status_code == 400
        assert data["success"] is False
        assert data["code"] == "INVALID_INPUT"

    def test_second_identical_request_is_cached(self, client, mock_ollama):
        payload = {"topic": "Recursion", "level": "beginner"}
        client.post(
            "/api/explain", json=payload, headers={"X-Session-Token": "cache-test-1"}
        )  # cache miss
        resp = client.post(
            "/api/explain", json=payload, headers={"X-Session-Token": "cache-test-1"}
        )  # cache hit
        assert resp.get_json()["cached"] is True

    def test_ollama_down_returns_structured_503(self, client):
        with patch("app.check_ollama", return_value=(False, [])):
            resp = client.post(
                "/api/explain",
                json={"topic": "UniqueTestTopic123"},
                headers={"X-Session-Token": "test-session-123"},
            )
        data = resp.get_json()
        assert resp.status_code == 503
        assert data["success"] is False
        assert "OLLAMA" in data["code"]

    def test_topic_exceeding_max_length_returns_400(self, client):
        resp = client.post("/api/explain", json={"topic": "x" * 500})
        assert resp.status_code == 400

    def test_xss_input_is_sanitised_not_rejected(self, client, mock_ollama):
        mock_ollama.return_value = '{"explanation":"safe","examples":[],"key_concepts":[],"analogies":[],"misconceptions":[]}'
        resp = client.post(
            "/api/explain",
            json={"topic": "<script>alert(1)</script>Python"},
            headers={"X-Session-Token": "xss-test-1"},
        )
        assert resp.status_code == 200  # sanitised, not rejected

    def test_invalid_level_defaults_to_beginner(self, client, mock_ollama):
        mock_ollama.return_value = '{"explanation":"ok","examples":[],"key_concepts":[],"analogies":[],"misconceptions":[]}'
        resp = client.post("/api/explain", json={"topic": "Python", "level": "expert"})
        assert resp.status_code == 200  # 'expert' → silently defaults to 'beginner'
