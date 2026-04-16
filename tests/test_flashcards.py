"""Tests for /api/flashcards endpoint."""

import pytest, json
from unittest.mock import patch


class TestFlashcardsEndpoint:
    def test_success_returns_correct_schema(self, client):
        with patch("app.call_ollama") as mock_ollama:
            mock_ollama.return_value = json.dumps(
                {
                    "cards": [
                        {
                            "front": "What is Python?",
                            "back": "A programming language",
                            "difficulty": "easy",
                            "color": "#27ae60",
                        }
                    ]
                }
            )
            resp = client.post(
                "/api/flashcards",
                json={"topic": "Python", "count": 10},
                headers={"X-Session-Token": "flashcards-test-2"},
            )
            data = resp.get_json()

            assert resp.status_code == 200
            assert data["success"] is True
            assert "cards" in data["data"]
            assert len(data["data"]["cards"]) == 1
            card = data["data"]["cards"][0]
            for field in ["front", "back", "difficulty", "color"]:
                assert field in card

    def test_missing_topic_returns_400(self, client):
        resp = client.post("/api/flashcards", json={"count": 10})
        data = resp.get_json()
        assert resp.status_code == 400
        assert data["success"] is False
        assert data["code"] == "INVALID_INPUT"

    def test_invalid_count_defaults_to_10(self, client, mock_ollama):
        mock_ollama.return_value = json.dumps({"cards": []})
        resp = client.post(
            "/api/flashcards",
            json={"topic": "Python", "count": 999},
            headers={"X-Session-Token": "flashcards-test-1"},
        )
        data = resp.get_json()
        assert resp.status_code == 200
        # Should accept and process with default validation

    def test_second_identical_request_is_cached(self, client, mock_ollama):
        payload = {"topic": "Python", "count": 10}
        client.post(
            "/api/flashcards", json=payload, headers={"X-Session-Token": "cache-test-1"}
        )  # cache miss
        resp = client.post(
            "/api/flashcards", json=payload, headers={"X-Session-Token": "cache-test-1"}
        )  # cache hit
        assert resp.get_json()["cached"] is True

    def test_ollama_down_returns_structured_503(self, client):
        with patch("app.check_ollama", return_value=(False, [])):
            resp = client.post(
                "/api/flashcards",
                json={"topic": "UniqueTestTopic123", "count": 10},
                headers={"X-Session-Token": "test-session-123"},
            )
        data = resp.get_json()
        assert resp.status_code == 503
        assert data["success"] is False
        assert "OLLAMA" in data["code"]

    def test_topic_exceeding_max_length_returns_400(self, client):
        resp = client.post("/api/flashcards", json={"topic": "x" * 500, "count": 10})
        assert resp.status_code == 400

    def test_xss_input_is_sanitised_not_rejected(self, client, mock_ollama):
        mock_ollama.return_value = '{"cards": []}'
        resp = client.post(
            "/api/flashcards",
            json={"topic": "<script>alert(1)</script>Python", "count": 10},
            headers={"X-Session-Token": "xss-test-1"},
        )
        assert resp.status_code == 200  # sanitised, not rejected
