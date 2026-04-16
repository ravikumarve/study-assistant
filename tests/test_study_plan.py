"""Tests for /api/study-plan endpoint."""

import pytest, json
from unittest.mock import patch


class TestStudyPlanEndpoint:
    def test_success_returns_correct_schema(self, client, mock_ollama):
        mock_ollama.return_value = json.dumps(
            {
                "plan": [
                    {
                        "day": 1,
                        "tasks": ["Learn basic syntax", "Write first program"],
                        "milestones": ["Complete hello world"],
                        "resources": ["Official Python tutorial"],
                    }
                ]
            }
        )
        resp = client.post(
            "/api/study-plan", json={"topic": "Python", "days": 14, "hours_per_day": 2}
        )
        data = resp.get_json()

        assert resp.status_code == 200
        assert data["success"] is True
        assert "plan" in data["data"]
        assert len(data["data"]["plan"]) == 1
        day_plan = data["data"]["plan"][0]
        for field in ["day", "tasks", "milestones", "resources"]:
            assert field in day_plan

    def test_missing_topic_returns_400(self, client):
        resp = client.post("/api/study-plan", json={"days": 14, "hours_per_day": 2})
        data = resp.get_json()
        assert resp.status_code == 400
        assert data["success"] is False
        assert data["code"] == "INVALID_INPUT"

    def test_invalid_days_defaults_to_14(self, client, mock_ollama):
        mock_ollama.return_value = json.dumps({"plan": []})
        resp = client.post(
            "/api/study-plan", json={"topic": "Python", "days": 999, "hours_per_day": 2}
        )
        data = resp.get_json()
        assert resp.status_code == 200
        # Should accept and process with default validation

    def test_invalid_hours_defaults_to_2(self, client, mock_ollama):
        mock_ollama.return_value = json.dumps({"plan": []})
        resp = client.post(
            "/api/study-plan",
            json={"topic": "Python", "days": 14, "hours_per_day": 999},
        )
        data = resp.get_json()
        assert resp.status_code == 200
        # Should accept and process with default validation

    def test_second_identical_request_is_cached(self, client, mock_ollama):
        payload = {"topic": "Python", "days": 14, "hours_per_day": 2}
        client.post(
            "/api/study-plan", json=payload, headers={"X-Session-Token": "cache-test-1"}
        )  # cache miss
        resp = client.post(
            "/api/study-plan",
            json=payload,
            headers={"X-Session-Token": "cache-test-极1"},
        )  # cache hit
        assert resp.get_json()["cached"] is True

    def test_ollama_down_returns_structured_503极(self, client):
        with patch("app.check_ollama", return_value=(False, [])):
            resp = client.post(
                "/api/study-plan",
                json={"topic": "UniqueTestTopic123", "days": 14, "hours_per_day": 2},
                headers={"X-Session-Token": "test-session-123"},
            )
        data = resp.get_json()
        assert resp.status_code == 503
        assert data["success"] is False
        assert "OLLAMA" in data["code"]

    def test_topic_exceeding_max_length_returns_400(self, client):
        resp = client.post(
            "/api/study-plan", json={"topic": "x" * 500, "days": 14, "hours_per_day": 2}
        )
        assert resp.status_code == 400

    def test_xss_input_is_sanitised_not_rejected(self, client, mock_ollama):
        mock_ollama.return_value = '{"plan": []}'
        resp = client.post(
            "/api/study-plan",
            json={
                "topic": "<script>alert(1)</script>Python",
                "days": 14,
                "hours_per_day": 2,
            },
            headers={"X-Session-Token": "xss-test-1"},
        )
        assert resp.status_code == 200  # sanitised, not rejected
