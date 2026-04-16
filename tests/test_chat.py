"""Tests for /api/chat endpoint."""

import pytest, json
from unittest.mock import patch


class TestChatEndpoint:
    def test_success_returns_correct_schema(self, client, mock_ollama, mock_rate_limit):
        mock_ollama.return_value = json.dumps(
            {
                "response": "Python is a great programming language for beginners.",
                "suggestions": ["Learn basic syntax", "Try small projects"],
            }
        )
        resp = client.post(
            "/api/chat",
            json={"message": "What is Python?", "history": []},
            headers={"X-Session-Token": "test-session-123"},
        )
        data = resp.get_json()

        assert resp.status_code == 200
        assert data["success"] is True
        for field in ["response", "suggestions"]:
            assert field in data["data"]

    def test_missing_message_returns_400(self, client, mock_rate_limit):
        resp = client.post("/api/chat", json={"history": []})
        data = resp.get_json()
        assert resp.status_code == 400
        assert data["success"] is False
        assert data["code"] == "INVALID_INPUT"

    def test_message_exceeding_max_length_returns_400(self, client, mock_rate_limit):
        resp = client.post("/api/chat", json={"message": "x" * 3000, "history": []})
        assert resp.status_code == 400

    def test_chat_not_cached(self, client, mock_ollama, mock_rate_limit):
        mock_ollama.return_value = json.dumps(
            {"response": "test response", "suggestions": []}
        )
        payload = {"message": "What is Python?", "history": []}
        client.post(
            "/api/chat", json=payload, headers={"X-Session-Token": "cache-test-1"}
        )  # should not be cached
        resp = client.post(
            "/api/chat", json=payload, headers={"X-Session-Token": "cache-test-1"}
        )  # should not be cached hit
        assert resp.get_json()["cached"] is False  # Chat should never be cached

    def test_ollama_down_returns_structured_503(self, client):
        with patch("app.check_ollama", return_value=(False, [])):
            resp = client.post(
                "/api/chat",
                json={"message": "Unique test message for testing.", "history": []},
                headers={"X-Session-Token": "test-session-123"},
            )
        data = resp.get_json()
        assert resp.status_code == 503
        assert data["success"] is False
        assert "OLLAMA" in data["code"]

    def test_xss_input_is_sanitised_not_rejected(
        self, client, mock_ollama, mock_rate_limit
    ):
        mock_ollama.return_value = '{"response": "safe", "suggestions": []}'
        resp = client.post(
            "/api/chat",
            json={"message": "<script>alert(1)</script>What is Python?", "history": []},
            headers={"X-Session-Token": "xss-test-1"},
        )
        assert resp.status_code == 200  # sanitised, not rejected

    def test_with_history_context(self, client, mock_ollama, mock_rate_limit):
        mock_ollama.return_value = json.dumps(
            {"response": "Python is interpreted.", "suggestions": []}
        )
        resp = client.post(
            "/api/chat",
            json={
                "message": "Is it compiled or interpreted?",
                "history": [
                    {"role": "user", "content": "What is Python?"},
                    {
                        "role": "assistant",
                        "content": "Python is a programming language.",
                    },
                ],
            },
        )
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["success"] is True
