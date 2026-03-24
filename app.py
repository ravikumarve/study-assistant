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


# Serve main application
@app.route("/")
def serve_index():
    return app.send_static_file("index.html")


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

    # Create indexes for cache table
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_key ON cache(key)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at)")

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

    # Create indexes for user progress table
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_progress_topic ON user_progress(topic)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_progress_created ON user_progress(created_at)"
    )

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
    """Get cached value or None."""
    conn = get_db()
    row = conn.execute(
        "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
    ).fetchone()

    if row is None:
        return None

    if datetime.fromisoformat(row["expires_at"]) < datetime.utcnow():
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


def cache_cleanup():
    """Clean up expired cache entries. Runs periodically."""
    conn = get_db()
    try:
        result = conn.execute(
            "DELETE FROM cache WHERE expires_at < ?", (datetime.utcnow().isoformat(),)
        )
        conn.commit()
        return result.rowcount
    except Exception:
        return 0


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
            "INSERT INTO study_sessions "
            "(session_token, started_at, last_active, activity_count) "
            "VALUES (?, ?, ?, 1)",
            (session_token, current_time, current_time),
        )
        conn.commit()
        return True

    # Check if we need to reset counter (new minute)
    last_active = datetime.fromisoformat(session["last_active"])
    if (current_time - last_active).total_seconds() >= 60:
        # Reset counter
        conn.execute(
            "UPDATE study_sessions SET "
            "activity_count = 1, last_active = ? "
            "WHERE session_token = ?",
            (current_time, session_token),
        )
        conn.commit()
        return True

    # Check current count
    if session["activity_count"] >= RATE_LIMIT_PER_MINUTE:
        return False

    # Increment counter
    conn.execute(
        "UPDATE study_sessions SET "
        "activity_count = activity_count + 1, "
        "last_active = ? WHERE session_token = ?",
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
            return (
                jsonify(
                    {
                        "success": False,
                        "error": str(e),
                        "code": "RATE_LIMITED",
                        "retry_after": 60,
                    }
                ),
                429,
            )
        except OllamaError as e:
            return jsonify(
                {"success": False, "error": str(e), "code": "OLLAMA_UNAVAILABLE"}
            ), 503
        except Exception as e:
            # Log internal errors but don't expose details
            app.logger.error(f"Internal error: {e}")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Internal server error",
                        "code": "INTERNAL_ERROR",
                    }
                ),
                500,
            )

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


# AI Prompt Templates
EXPLAIN_PROMPT = """
Create a comprehensive explanation for a {level} learner about: {topic}

Please provide:
1. A clear, concise explanation
2. 2-3 practical examples
3. 3-5 key concepts to remember
4. 1-2 helpful analogies
5. Common misconceptions to avoid
6. Confidence score (0-100) based on accuracy
7. Estimated study time in minutes for this topic

Format the response as valid JSON with these exact keys:
{{
  "explanation": "string",
  "examples": ["string1", "string2", ...],
  "key_concepts": ["string1", "string2", ...],
  "analogies": ["string1", "string2", ...],
  "misconceptions": ["string1", "string2", ...],
  "confidence_score": 85,
  "estimated_study_time": 30,
  "complexity_level": "beginner|intermediate|advanced"
}}
"""

QUIZ_PROMPT = """
Create a {count}-question quiz about {topic} at {极difficulty} difficulty level.

For each question, provide:
- A clear question
- 4 multiple choice options (A, B, C, D)
- The correct answer (letter only)
- A brief explanation
- An optional hint

Also provide:
- Overall confidence score (0-100) for quiz accuracy
- Estimated completion time in minutes
- Complexity assessment

Format as valid JSON with this structure:
{{
  "questions": [
    {{
      "question": "string",
      "options": ["A: option1", "B: option2", "C: option3", "D: option4"],
      "answer": "A",
      "explanation": "string",
      "hint": "string"
    }}
  ],
  "confidence_score": 90,
  "estimated_completion_time": 15,
  "complexity_level": "beginner|intermediate|advanced",
  "total_score": 100
}}
"""

FLASHCARD_PROMPT = """
Create {count} flashcards about {topic}.

Each flashcard should have:
- Front: Question or term
- Back: Detailed explanation or definition
- Difficulty level (easy, medium, hard)
- Color category for organization

Also provide:
- Overall confidence score (0-100) for content accuracy
- Estimated study time in minutes for the full set
- Recommended study approach

Format as valid JSON:
{{
  "cards": [
    {{
      "front": "string",
      "back": "string",
      "difficulty": "easy|medium|hard",
      "color": "blue|green|red|purple|orange"
    }}
  ],
  "confidence_score": 88,
  "estimated_study_time": 25,
  "study_approach": "spaced_repetition|active_recall|mixed",
  "complexity_level": "beginner|intermediate|advanced"
}}
"""

STUDY_PLAN_PROMPT = """
Create a {days}-day study plan for learning {topic} with {hours_per_day} hours per day.

For each day, include:
- Specific learning tasks
- Milestones to achieve
- Recommended resources
- Time allocation suggestions

Also provide:
- Confidence score (0-100) for plan effectiveness
- Total estimated hours for completion
- Success probability based on typical learners
- Prerequisite knowledge assessment

Format as valid JSON:
{{
  "plan": [
    {{
      "day": 1,
      "tasks": ["string1", "string2", ...],
      "milestones": ["string1", "string2", ...],
      "resources": ["string1", "string2", ...],
      "estimated_hours": 2
    }}
  ],
  "confidence_score": 92,
  "total_estimated_hours": 14,
  "success_probability": 85,
  "prerequisite_level": "beginner|intermediate|advanced",
  "complexity_level": "beginner|intermediate|advanced"
}}
"""

MIND_MAP_PROMPT = """
Create a mind map structure for {topic}.

Include:
- Central concept
- Main branches with labels and colors
- Sub-branches with children
- Logical organization
- Confidence score (0-100) based on knowledge accuracy
- Estimated study time in minutes

Format as valid JSON:
{{
  "center": "string",
  "branches": [
    {{
      "label": "string",
      "color": "blue|green|red|purple|orange|yellow",
      "children": ["string1", "string2", ...]
    }}
  ],
  "confidence_score": 85,
  "estimated_study_time": 45,
  "complexity_level": "beginner|intermediate|advanced"
}}
"""

SUMMARY_PROMPT = """
Summarize the following notes in {format} format:

{notes}

Provide:
- Concise summary
- Key points
- Format used
- Confidence score (0-100) for summary accuracy
- Estimated reading time in minutes
- Information density assessment
- Key takeaways

Format as valid JSON:
{{
  "summary": "string",
  "key_points": ["string1", "string2", ...],
  "format_used": "bullet|paragraph|outline|cornell",
  "confidence_score": 95,
  "estimated_reading_time": 5,
  "information_density": "high|medium|low",
  "key_takeaways": ["string1", "string2", ...],
  "complexity_level": "beginner|intermediate|advanced"
}}
"""

CHAT_PROMPT = """
You are a helpful study assistant. Continue the conversation:

Previous messages:
{history}

User message: {message}

Respond helpfully and suggest 2-3 follow-up questions.

Format as valid JSON:
{{
  "response": "string",
  "suggestions": ["string1", "string2", ...]
}}
"""


def parse_ai_response(response_text: str) -> dict:
    """Parse AI response and extract JSON, with fallback handling."""
    import re

    # First, try to parse the entire text as JSON
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code blocks
    try:
        # Remove markdown code blocks
        clean_text = re.sub(r"```(?:json)?\s*", "", response_text)
        clean_text = re.sub(r"\s*```", "", clean_text)
        clean_text = clean_text.strip()

        # Try to parse cleaned text
        return json.loads(clean_text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object pattern
    try:
        json_match = re.search(r"\{[^{}]*\}", response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except json.JSONDecodeError:
        pass

    # Final fallback: try to clean and parse
    try:
        clean_text = response_text.strip()
        # Remove any non-JSON content before {
        clean_text = clean_text[clean_text.find("{") :]
        # Remove any non-JSON content after }
        if "}" in clean_text:
            clean_text = clean_text[: clean_text.rfind("}") + 1]

        # Fix common formatting issues
        clean_text = re.sub(r",\s*\}", "}", clean_text)  # Remove trailing commas
        clean_text = re.sub(
            r",\s*\]", "]", clean_text
        )  # Remove trailing commas in arrays
        clean_text = re.sub(r"'\s*:", '":', clean_text)  # Fix single quotes to double
        clean_text = re.sub(r":\s*'", ':"', clean_text)  # Fix single quotes to double

        return json.loads(clean_text)
    except (json.JSONDecodeError, ValueError):
        raise ValidationError("AI response could not be parsed as valid JSON")


def call_ai_endpoint(endpoint: str, params: dict, prompt_template: str) -> dict:
    """Common function to handle AI endpoint calls with caching."""
    # Validate input
    topic = validate_topic(params.get("topic", ""))

    # Check cache first
    cache_key = make_cache_key(endpoint, params)
    cached = cache_get(cache_key)
    if cached:
        return {"data": cached, "cached": True}

    # Check rate limiting
    session_token = request.headers.get("X-Session-Token")
    if not session_token or not check_rate_limit(session_token):
        raise RateLimitError("Rate limit exceeded. Please try again in a minute.")

    # Check Ollama availability
    available, _ = check_ollama()
    if not available:
        raise OllamaError(
            "Ollama is not available. Please start Ollama with: ollama serve"
        )

    # Prepare prompt
    prompt = prompt_template.format(**params)

    # Call Ollama
    response_text = call_ollama(prompt)

    # Parse response
    ai_data = parse_ai_response(response_text)

    # Cache successful response
    cache_set(cache_key, ai_data)

    # Log progress
    if session_token:
        conn = get_db()
        conn.execute(
            "INSERT INTO user_progress (topic, activity, metadata) VALUES (?, ?, ?)",
            (topic, endpoint.replace("/api/", ""), json.dumps({"params": params})),
        )
        conn.commit()

    return {"data": ai_data, "cached": False}


# Core AI Endpoints
@app.route("/api/explain", methods=["POST"])
@handle_errors
def explain_topic():
    """Get detailed explanation of a topic."""
    data = request.get_json()
    topic = validate_topic(data.get("topic"))
    level = validate_level(data.get("level"))

    result = call_ai_endpoint(
        "/api/explain", {"topic": topic, "level": level}, EXPLAIN_PROMPT
    )

    return jsonify(
        {
            "success": True,
            "data": result["data"],
            "cached": result["cached"],
            "provider": "ollama",
        }
    )


@app.route("/api/quiz", methods=["POST"])
@handle_errors
def generate_quiz():
    """Generate quiz questions on a topic."""
    data = request.get_json()
    topic = validate_topic(data.get("topic"))
    count = validate_count(data.get("count"), 3, 10, 5)
    difficulty = data.get("difficulty", "medium")

    result = call_ai_endpoint(
        "/api/quiz",
        {"topic": topic, "count": count, "difficulty": difficulty},
        QUIZ_PROMPT,
    )

    return jsonify(
        {
            "success": True,
            "data": result["data"],
            "cached": result["cached"],
            "provider": "ollama",
        }
    )


@app.route("/api/flashcards", methods=["POST"])
@handle_errors
def generate_flashcards():
    """Generate flashcards for a topic."""
    data = request.get_json()
    topic = validate_topic(data.get("topic"))
    count = validate_count(data.get("count"), 5, 20, 10)

    result = call_ai_endpoint(
        "/api/flashcards", {"topic": topic, "count": count}, FLASHCARD_PROMPT
    )

    return jsonify(
        {
            "success": True,
            "data": result["data"],
            "cached": result["cached"],
            "provider": "ollama",
        }
    )


@app.route("/api/study-plan", methods=["POST"])
@handle_errors
def generate_study_plan():
    """Generate study plan for a topic."""
    data = request.get_json()
    topic = validate_topic(data.get("topic"))
    days = validate_count(data.get("days"), 1, 30, 7)
    hours_per_day = validate_count(data.get("hours_per_day"), 1, 8, 2)

    result = call_ai_endpoint(
        "/api/study-plan",
        {"topic": topic, "days": days, "hours_per_day": hours_per_day},
        STUDY_PLAN_PROMPT,
    )

    return jsonify(
        {
            "success": True,
            "data": result["data"],
            "cached": result["cached"],
            "provider": "ollama",
        }
    )


@app.route("/api/mind-map", methods=["POST"])
@handle_errors
def generate_mind_map():
    """Generate mind map for a topic."""
    data = request.get_json()
    topic = validate_topic(data.get("topic"))

    result = call_ai_endpoint("/api/mind-map", {"topic": topic}, MIND_MAP_PROMPT)

    return jsonify(
        {
            "success": True,
            "data": result["data"],
            "cached": result["cached"],
            "provider": "ollama",
        }
    )


@app.route("/api/summarize", methods=["POST"])
@handle_errors
def summarize_notes():
    """Summarize provided notes."""
    data = request.get_json()
    notes = validate_notes(data.get("notes"))
    format = data.get("format", "bullet")

    if format not in VALID_FORMATS:
        format = "bullet"

    # Summarize endpoint doesn't use topic, so handle specially
    cache_key = make_cache_key("/api/summarize", {"notes": notes, "format": format})
    cached = cache_get(cache_key)
    if cached:
        return jsonify(
            {"success": True, "data": cached, "cached": True, "provider": "ollama"}
        )

    # Check rate limiting
    session_token = request.headers.get("X-Session-Token")
    if not session_token or not check_rate_limit(session_token):
        raise RateLimitError("Rate limit exceeded. Please try again in a minute.")

    # Check Ollama availability
    available, _ = check_ollama()
    if not available:
        raise OllamaError(
            "Ollama is not available. Please start Ollama with: ollama serve"
        )

    # Prepare prompt
    prompt = SUMMARY_PROMPT.format(notes=notes, format=format)

    # Call Ollama
    response_text = call_ollama(prompt)

    # Parse response
    ai_data = parse_ai_response(response_text)

    # Cache successful response
    cache_set(cache_key, ai_data)

    # Log progress
    if session_token:
        conn = get_db()
        conn.execute(
            "INSERT INTO user_progress (topic, activity, metadata) VALUES (?, ?, ?)",
            ("notes summary", "summary", json.dumps({"notes_length": len(notes)})),
        )
        conn.commit()

    return jsonify(
        {"success": True, "data": ai_data, "cached": False, "provider": "ollama"}
    )


@app.route("/api/chat", methods=["POST"])
@handle_errors
def chat_assistant():
    """Conversational chat with study assistant."""
    data = request.get_json()
    message = data.get("message", "").strip()
    history = data.get("history", [])

    if not message:
        raise ValidationError("Message is required for chat")

    if len(message) > MAX_MESSAGE_LENGTH:
        raise ValidationError(f"Message must be under {MAX_MESSAGE_LENGTH} characters")

    # Chat is not cached due to conversational context
    session_token = request.headers.get("X-Session-Token")
    if not session_token or not check_rate_limit(session_token):
        raise RateLimitError("Rate limit exceeded. Please try again in a minute.")

    available, _ = check_ollama()
    if not available:
        raise OllamaError(
            "Ollama is not available. Please start Ollama with: ollama serve"
        )

    prompt = CHAT_PROMPT.format(message=message, history=json.dumps(history))
    response_text = call_ollama(prompt)
    ai_data = parse_ai_response(response_text)

    # Log chat activity (but don't cache)
    if session_token:
        conn = get_db()
        conn.execute(
            "INSERT INTO user_progress (topic, activity, metadata) VALUES (?, ?, ?)",
            ("chat conversation", "chat", json.dumps({"message_length": len(message)})),
        )
        conn.commit()

    return jsonify(
        {"success": True, "data": ai_data, "cached": False, "provider": "ollama"}
    )


@app.route("/api/progress", methods=["GET"])
@handle_errors
def get_progress():
    """Get user progress statistics."""
    session_token = request.headers.get("X-Session-Token")
    if not session_token:
        raise ValidationError("Session token required")

    conn = get_db()

    # Get recent activities
    activities = conn.execute(
        "SELECT topic, activity, score, created_at FROM user_progress "
        "WHERE created_at >= datetime('now', '-7 days') "
        "ORDER BY created_at DESC LIMIT 20"
    ).fetchall()

    # Get activity breakdown
    breakdown = conn.execute(
        "SELECT activity, COUNT(*) as count FROM user_progress "
        "WHERE created_at >= datetime('now', '-30 days') "
        "GROUP BY activity"
    ).fetchall()

    # Get streak
    streak = conn.execute(
        "SELECT COUNT(DISTINCT date(created_at)) as streak "
        "FROM user_progress "
        "WHERE created_at >= datetime('now', '-30 days') "
        "ORDER BY created_at DESC"
    ).fetchone()

    return jsonify(
        {
            "success": True,
            "data": {
                "recent_activities": [dict(act) for act in activities],
                "activity_breakdown": {
                    act["activity"]: act["count"] for act in breakdown
                },
                "streak_days": streak["streak"] if streak else 0,
            },
        }
    )


@app.route("/api/progress", methods=["POST"])
@handle_errors
def log_progress():
    """Log user progress for an activity."""
    data = request.get_json()
    topic = validate_topic(data.get("topic"))
    activity = data.get("activity", "")
    score = data.get("score")

    if activity not in VALID_ACTIVITIES:
        raise ValidationError(
            f"Invalid activity. Must be one of: {list(VALID_ACTIVITIES)}"
        )

    conn = get_db()
    conn.execute(
        "INSERT INTO user_progress (topic, activity, score) VALUES (?, ?, ?)",
        (topic, activity, score),
    )
    conn.commit()

    return jsonify({"success": True, "saved": True})


if __name__ == "__main__":
    with app.app_context():
        db_init()
        # Clean up expired cache entries on startup
        cleaned = cache_cleanup()
        if cleaned > 0:
            print(f"Cleaned up {cleaned} expired cache entries")

    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    app.run(host="0.0.0.0", port=port, debug=debug)


def create_app(config=None):
    """Application factory function for testing."""
    # Create a new Flask app instance
    new_app = Flask(__name__)

    if config:
        new_app.config.update(config)
    else:
        new_app.config["TESTING"] = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    # Import and register all routes from the global app to the new app
    from flask import current_app

    # Copy all routes from the global app to the new app
    for rule in app.url_map.iter_rules():
        if rule.endpoint != "static":
            view_func = app.view_functions[rule.endpoint]
            new_app.add_url_rule(
                rule.rule,
                endpoint=rule.endpoint,
                view_func=极view_func,
                methods=rule.methods,
            )

    return new_app
