"""Tests for /api/summarize endpoint."""

import pytest, json
from unittest.mock import patch


class TestSummarizeEndpoint:
    def test_success_returns_correct_schema(self, client, mock_ollama):
        mock_ollama.return_value = json.dumps(
            {
                "summary": "Python is a versatile programming language.",
                "key_points": ["Easy to learn", "Large community", "Many libraries"],
                "format_used": "bullet",
            }
        )
        resp = client.post(
            "/api/summarize",
            json={
                "notes": "Python is great for beginners. It has many libraries.",
                "format": "bullet",
            },
        )
        data = resp.get_json()

        assert resp.status_code == 200
        assert data["success"] is True
        for field in ["summary", "key_points", "format_used"]:
            assert field in data["data"]

    def test_missing_notes_returns_400(self, client):
        resp = client.post("/api/summarize", json={"format": "bullet"})
        data = resp.get_json()
        assert resp.status_code == 400
        assert data["success"] is False
        assert data["code"] == "INVALID_INPUT"

    def test_invalid_format_defaults_to_bullet(self, client, mock_ollama):
        mock_ollama.return_value = json.dumps(
            {"summary": "test", "key_points": [], "format_used": "bullet"}
        )
        resp = client.post(
            "/api/summarize", json={"notes": "Test notes", "format": "invalid"}
        )
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["data"]["format_used"] == "bullet"

    def test_second_identical_request_is_cached(self, client, mock_ollama):
        payload = {
            "notes": "Python is great for beginners. It has many libraries.",
            "format": "bullet",
        }
        client.post(
            "/api/summarize", json=payload, headers={"X-Session-Token": "cache-test-1"}
        )  # cache miss
        resp = client.post(
            "/api/summarize", json=payload, headers={"X-Session-Token": "cache-test-1"}
        )  # cache hit
        assert resp.get_json()["cached"] is True

    def test_ollama_down_returns_structured_503(self, client):
        with patch("app.check_ollama", return_value=(False, [])):
            resp = client.post(
                "/api/summarize",
                json={
                    "notes": "Unique test notes content for testing.",
                    "format": "bullet",
                },
                headers={"X-Session-Token": "test-session-123"},
            )
        data = resp.get_json()
        assert resp.status_code == 503
        assert data["success"] is False
        assert "OLLAMA" in data["code"]

    def test_notes_exceeding_max_length_returns_400(self, client):
        resp = client.post(
            "/api/summarize", json={"notes": "x" * 15000, "format": "bullet"}
        )
        assert resp.status_code == 400

    def test_xss_input_is_sanitised_not_rejected(self, client, mock_ollama):
        mock_ollama.return_value = (
            '{"summary": "safe", "key_points": [], "format_used": "bullet"}'
        )
        resp = client.post(
            "/api/summarize",
            json={
                "notes": "<script>alert(1)</script>Python is great",
                "format": "bullet",
            },
            headers={"X-Session-Token": "xss-test-1"},
        )
        assert resp.status_code == 200  # sanitised, not rejected
