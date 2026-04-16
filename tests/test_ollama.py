"""Tests for Ollama integration."""

import pytest, json
from unittest.mock import patch, MagicMock
import requests


class TestOllamaIntegration:
    def test_check_ollama_available(self, client):
        from app import check_ollama

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "models": [{"name": "deepseek-r1:7b"}]
            }

            available, models = check_ollama()
            assert available is True
            assert "deepseek-r1:7b" in models

    def test_check_ollama_unavailable(self, client):
        from app import check_ollama

        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.ConnectionError("Connection refused")

            available, models = check_ollama()
            assert available is False
            assert models == []

    def test_call_ollama_success(self, client):
        from app import call_ollama

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"response": "test response"}

            result = call_ollama("test prompt")
            assert result == "test response"
