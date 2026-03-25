"""Tests for /api/mind-map endpoint."""

import pytest, json
from unittest.mock import patch


class TestMindMapEndpoint:
    def test_success_returns_correct_schema(self, client, mock_ollama):
        mock_ollama.return_value = json.dumps(
            {
                "center": "Python Programming",
                "branches": [
                    {
                        "label": "Syntax",
                        "color": "#6c63ff",
                        "children": ["Variables", "Functions", "Classes"],
                    }
                ],
            }
        )
        resp = client.post("/api/mind-map", json={"topic": "Python"})
        data = resp.get_json()

        assert resp.status_code == 200
        assert data["success"] is True
        assert "center" in data["data"]
        assert "branches" in data["data"]
        assert len(data["data"]["branches"]) == 1
        branch = data["data"]["branches"][0]
        for field in ["label", "color", "children"]:
            assert field in branch

    def test_missing_topic_returns_400(self, client):
        resp = client.post("/api/mind-map", json={})
        data = resp.get_json()
        assert resp.status_code == 400
        assert data["success"] is False
        assert data["code"] == "INVALID_INPUT"

    def test_second_identical_request_is_cached(self, client, mock_ollama):
        payload = {"topic": "Python"}
        client.post(
            "/api/mind-map", json=payload, headers={"X-Session-Token": "cache-test-1"}
        )  # cache miss
        resp = client.post(
            "/api/mind-map", json=payload, headers={"X-Session-Token": "cache-test-1"}
        )  # cache hit
        assert resp.get_json()["cached"] is True

    def test_ollama_down_returns_structured_503(self, client):
        with patch("app.check_ollama", return_value=(False, [])):
            resp = client.post(
                "/api/mind-map",
                json={"topic": "UniqueTestTopic123"},
                headers={"X-Session-Token": "test-session-123"},
            )
        data = resp.get_json()
        assert resp.status_code == 503
        assert data["success"] is False
        assert "OLLAMA" in data["code"]

    def test_topic_exceeding_max_length_returns_400(self, client):
        resp = client.post("/api/mind-map", json={"topic": "极x" * 500})
        assert resp.status_code == 400

    def test_xss_input_is_sanitised_not_rejected(self, client, mock_ollama):
        mock_ollama.return_value = '{"center": "safe", "branches": []}'
        resp = client.post(
            "/api/mind-map",
            json={"topic": "<script>alert(1)</script>Python"},
            headers={"X-Session-Token": "xss-test-1"},
        )
        assert resp.status_code == 200  # sanitised, not rejected
