#!/usr/bin/env python3
"""
Advanced AI Study Assistant Pro
Flask application with SQLite database, caching, and Ollama integration.
"""

import os
import sqlite3
import hashlib
import json
import time
from datetime import datetime, timedelta
from functools import wraps

import bleach
from flask import Flask, request, jsonify, g

# Configuration constants
MAX_TOPIC_LENGTH = 200
MAX_NOTES_LENGTH = 10000
MAX_MESSAGE_LENGTH = 2000
VALID_LEVELS = {"beginner", "intermediate", "advanced"}
VALID_ACTIVITIES = {
    "explanation",
    "quiz",
    "flashcard",
    "study_plan",
    "mind_map",
    "summary",
    "chat",
}
VALID_FORMATS = {"bullet", "paragraph", "outline", "cornell"}

# Environment variables with defaults
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:7b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "90"))
OLLAMA_MAX_RETRIES = 2
CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
DATABASE_URL = os.getenv("DATABASE", "study_assistant.db")

# Create Flask application
app = Flask(__name__)
app.config["TESTING"] = os.getenv("FLASK_DEBUG", "false").lower() == "true"


# Custom exceptions
class OllamaError(Exception):
    """Raised for all Ollama failures. Message is user-safe."""

    pass


class ValidationError(Exception):
    """Raised for input validation failures."""

    pass


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""

    pass


# Database connection management
def get_db():
    """Get SQLite database connection with row factory."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE_URL)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    """Close database connection at end of request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def db_init():
    """Initialize database tables."""
    conn = get_db()

    # Cache table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL
        )
    """)

    # User progress table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            activity TEXT NOT NULL,
            score REAL,
            duration INTEGER,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Study sessions table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_token TEXT UNIQUE NOT NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            activity_count INTEGER DEFAULT 0
        )
    """)

    conn.commit()


# Input validation functions
def validate_topic(raw: str) -> str:
    """Validate and sanitize topic input."""
    if not raw or not isinstance(raw, str):
        raise ValidationError("Topic is required.")

    clean = bleach.clean(raw.strip())
    if len(clean) < 2:
        raise ValidationError("Topic must be at least 2 characters.")
    if len(clean) > MAX_TOPIC_LENGTH:
        raise ValidationError(f"Topic must be under {MAX_TOPIC_LENGTH} characters.")

    return clean


def validate_level(raw: str | None) -> str:
    """Validate and normalize level input."""
    if not raw:
        return "beginner"

    lvl = raw.lower().strip()
    return lvl if lvl in VALID_LEVELS else "beginner"


def validate_count(raw, min_val: int, max_val: int, default: int) -> int:
    """Validate count input within range."""
    try:
        return max(min_val, min(max_val, int(raw)))
    except (TypeError, ValueError):
        return default


def validate_notes(raw: str) -> str:
    """Validate and sanitize notes input."""
    if not raw or not isinstance(raw, str):
        raise ValidationError("Notes text is required.")

    if len(raw) > MAX_NOTES_LENGTH:
        raise ValidationError(f"Notes must be under {MAX_NOTES_LENGTH} characters.")

    return bleach.clean(raw.strip())


# Cache system
def make_cache_key(endpoint: str, params: dict) -> str:
    """Create deterministic cache key from endpoint and parameters."""
    canonical = json.dumps({"endpoint": endpoint, **params}, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def cache_get(key: str) -> dict | None:
    """Get cached value or None. Lazily deletes expired entries."""
    conn = get_db()
    row = conn.execute(
        "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
    ).fetchone()

    if row is None:
        return None

    if datetime.fromisoformat(row["expires_at"]) < datetime.utcnow():
        conn.execute("DELETE FROM cache WHERE key = ?", (key,))
        conn.commit()
        return None

    return json.loads(row["value"])


def cache_set(key: str, value: dict, ttl_hours: int = CACHE_TTL_HOURS) -> None:
    """Upsert cache entry. Silently fails on write errors."""
    try:
        expires = datetime.utcnow() + timedelta(hours=ttl_hours)
        conn = get_db()
        conn.execute(
            """INSERT INTO cache (key, value, expires_at) VALUES (?, ?, ?)
               ON CONFLICT(key) DO UPDATE SET
                   value=excluded.value, expires_at=excluded.expires_at""",
            (key, json.dumps(value), expires.isoformat()),
        )
        conn.commit()
    except Exception:
        pass  # Cache write failure is non-fatal


# Rate limiting
def check_rate_limit(session_token: str) -> bool:
    """Check if session has exceeded rate limit."""
    conn = get_db()

    # Get or create session
    session = conn.execute(
        "SELECT * FROM study_sessions WHERE session_token = ?", (session_token,)
    ).fetchone()

    current_time = datetime.utcnow()

    if not session:
        # New session
        conn.execute(
            "INSERT INTO study_sessions (session_token, started_at, last_active, activity_count) VALUES (?, ?, ?, 1)",
            (session_token, current_time, current_time),
        )
        conn.commit()
        return True

    # Check if we need to reset counter (new minute)
    last_active = datetime.fromisoformat(session["last_active"])
    if (current_time - last_active).total_seconds() >= 60:
        # Reset counter
        conn.execute(
            "UPDATE study_sessions SET activity_count = 1, last_active = ? WHERE session_token = ?",
            (current_time, session_token),
        )
        conn.commit()
        return True

    # Check current count
    if session["activity_count"] >= RATE_LIMIT_PER_MINUTE:
        return False

    # Increment counter
    conn.execute(
        "UPDATE study_sessions SET activity_count = activity_count + 1, last_active = ? WHERE session_token = ?",
        (current_time, session_token),
    )
    conn.commit()
    return True


# Ollama integration
def check_ollama() -> tuple[bool, list[str]]:
    """Check Ollama availability and get available models."""
    try:
        import requests

        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            return True, models
        return False, []
    except Exception:
        return False, []


def call_ollama(prompt: str, model: str = None, max_tokens: int = 1000) -> str:
    """Call Ollama with retry + exponential backoff."""
    import requests

    target = model or OLLAMA_DEFAULT_MODEL

    for attempt in range(1, OLLAMA_MAX_RETRIES + 1):
        try:
            r = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": target,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": max_tokens,
                        "top_p": 0.9,
                    },
                },
                timeout=OLLAMA_TIMEOUT,
            )
            r.raise_for_status()
            return r.json()["response"].strip()
        except requests.Timeout:
            if attempt == OLLAMA_MAX_RETRIES:
                raise OllamaError(
                    f"Ollama timed out after {OLLAMA_TIMEOUT}s. Try a smaller model."
                )
            time.sleep(attempt * 2)
        except requests.ConnectionError:
            raise OllamaError("Ollama is not running. Start it with: ollama serve")
        except KeyError:
            raise OllamaError(
                "Unexpected response format from Ollama. Check your Ollama version."
            )
        except Exception as e:
            raise OllamaError(f"Ollama error: {type(e).__name__}")


# Error handling decorator
def handle_errors(f):
    """Decorator to handle common errors and return JSON responses."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            return jsonify(
                {"success": False, "error": str(e), "code": "INVALID_INPUT"}
            ), 400
        except RateLimitError as e:
            return jsonify(
                {
                    "success": False,
                    "error": str(e),
                    "code": "RATE_LIMITED",
                    "retry_after": 60,
                }
            ), 429
        except OllamaError as e:
            return jsonify(
                {"success": False, "error": str(e), "code": "OLLAMA_UNAVAILABLE"}
            ), 503
        except Exception as e:
            # Log internal errors but don't expose details
            app.logger.error(f"Internal error: {e}")
            return jsonify(
                {
                    "success": False,
                    "error": "Internal server error",
                    "code": "INTERNAL_ERROR",
                }
            ), 500

    return decorated_function


# Health check endpoint
@app.route("/api/health", methods=["GET"])
def health_check():
    """Simple health check endpoint."""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "ollama_available": check_ollama()[0],
        }
    )


# Ollama status endpoint
@app.route("/api/ollama/status", methods=["GET"])
@handle_errors
def ollama_status():
    """Check Ollama availability and get model list."""
    available, models = check_ollama()
    return jsonify(
        {
            "available": available,
            "models": models,
            "default_model": OLLAMA_DEFAULT_MODEL,
        }
    )


# Main application entry
if __name__ == "__main__":
    with app.app_context():
        db_init()

    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    app.run(host="0.0.0.0", port=port, debug=debug)
