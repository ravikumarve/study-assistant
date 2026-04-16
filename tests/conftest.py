"""Shared fixtures for all test modules."""

import pytest
from unittest.mock import patch
import os


@pytest.fixture(scope="session")
def app():
    """Flask app in test mode with in-memory SQLite. Session-scoped for speed."""
    import os
    import sys

    # Set environment variables before importing app
    os.environ["RATE_LIMIT_PER_MINUTE"] = "99999"

    sys.path.insert(0, "..")
    from app import app as flask_app

    # Configure app for testing
    flask_app.config.update(
        {
            "TESTING": True,
            "DATABASE": ":memory:",
            "RATE_LIMIT_PER_MINUTE": 99999,  # Disable rate limiting in tests
            "CACHE_TTL_HOURS": 24,
        }
    )

    # Disable rate limiting completely for tests
    import app

    app.RATE_LIMIT_PER_MINUTE = 99999

    # Initialize database
    with flask_app.app_context():
        from app import db_init

        db_init()

    # Monkey patch rate limiting for tests
    import app

    def always_allow_rate_limit(session_token):
        print(f"DEBUG: Rate limit check for {session_token} - ALWAYS ALLOWING")
        return True

    app.check_rate_limit = always_allow_rate_limit
    print("DEBUG: Rate limiting patched in app fixture")

    yield flask_app


@pytest.fixture
def client(app):
    """Fresh test client per test function."""
    with app.app_context():
        yield app.test_client()


@pytest.fixture
def mock_ollama():
    """Patch Ollama globally — tests NEVER hit real Ollama."""
    with patch("app.call_ollama") as mock:
        mock.return_value = '{"explanation":"test","examples":[],"key_concepts":[],"analogies":[],"misconceptions":[]}'
        yield mock


@pytest.fixture
def mock_rate_limit():
    """Patch rate limiting to always allow requests."""
    with patch("app.check_rate_limit", return_value=True) as mock:
        yield mock
