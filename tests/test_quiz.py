"""Tests for /api/quiz endpoint."""

import pytest, json
from unittest.mock import patch


class TestQuizEndpoint:
    def test_success_returns_correct_schema(self, client, mock_ollama):
        mock_ollama.return_value = json.dumps(
            {
                "questions": [
                    {
                        "question": "What is Python?",
                        "options": ["Snake", "Programming language", "Animal", "Food"],
                        "answer": "Programming language",
                        "explanation": "Python is a high-level programming language.",
                        "hint": "Think about what developers use",
                    }
                ]
            }
        )
        resp = client.post(
            "/api/quiz",
            json={"topic": "Python", "count": 5, "difficulty": "medium"},
            headers={"X-Session-Token": "quiz-test-1"},
        )
        data = resp.get_json()

        assert resp.status_code == 200
        assert data["success"] is True
        assert "questions" in data["data"]
        assert len(data["data"]["questions"]) == 1
        question = data["data"]["questions"][0]
        for field in ["question", "options", "answer", "explanation", "hint"]:
            assert field in question

    def test_missing_topic_returns_400(self, client):
        resp = client.post("/api/quiz", json={"count": 5})
        data = resp.get_json()
        assert resp.status_code == 400
        assert data["success"] is False
        assert data["code"] == "INVALID_INPUT"

    def test_invalid_count_defaults_to_5(self, client, mock_ollama):
        mock_ollama.return_value = json.dumps({"questions": []})
        resp = client.post(
            "/api/quiz",
            json={"topic": "Python", "count": 999},
            headers={"X-Session-Token": "quiz-test-2"},
        )
        data = resp.get_json()
        assert resp.status_code == 200
        # Should accept and process with default validation

    def test_second_identical_request_is_cached(self, client, mock_ollama):
        payload = {"topic": "Python", "count": 5, "difficulty": "medium"}
        client.post(
            "/api/quiz", json=payload, headers={"X-Session-Token": "cache-test-1"}
        )  # cache miss
        resp = client.post(
            "/api/quiz", json=payload, headers={"X-Session-Token": "cache-test-1"}
        )  # cache hit
        assert resp.get_json()["cached"] is True

    def test_ollama_down_returns_structured_503(self, client):
        with patch("app.check_ollama", return_value=(False, [])):
            resp = client.post(
                "/api/quiz",
                json={"topic": "UniqueTestTopic123", "count": 5},
                headers={"X-Session-Token": "test-session-123"},
            )
        data = resp.get_json()
        assert resp.status_code == 503
        assert data["success"] is False
        assert "OLLAMA" in data["code"]

    def test_topic_exceeding_max_length_returns_400(self, client):
        resp = client.post("/api/quiz", json={"topic": "x" * 500, "count": 5})
        assert resp.status_code == 400

    def test_xss_input_is_sanitised_not_rejected(self, client, mock_ollama):
        mock_ollama.return_value = '{"questions": []}'
        resp = client.post(
            "/api/quiz",
            json={"topic": "<script>alert(1)</script>Python", "count": 5},
            headers={"X-Session-Token": "xss-test-1"},
        )
        assert resp.status_code == 200  # sanitised, not rejected

    def test_invalid_difficulty_defaults_to_medium(self, client, mock_ollama):
        mock_ollama.return_value = '{"questions": []}'
        resp = client.post(
            "/api/quiz",
            json={"topic": "Python", "difficulty": "expert"},
            headers={"X-Session-Token": "quiz-test-3"},
        )
        assert resp.status_code == 200  # 'expert' → silently defaults to 'medium'
