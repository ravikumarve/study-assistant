# AGENTS.md — Advanced AI Study Assistant Pro
## Coding Intelligence File for opencode + DeepSeek

> **This file is the authoritative runtime spec for all AI coding agents.**
> Read this entire file before writing a single line of code. Never deviate from structure or patterns defined here without explicit instruction. When uncertain, reason step-by-step before acting.

---

## 🧠 AGENT IDENTITY & OPERATING CONTEXT

**Project:** Advanced AI Study Assistant Pro  
**Type:** Full-stack Flask + Vanilla JS single-page web application  
**Runtime:** opencode with DeepSeek V3 (`deepseek-chat`) or DeepSeek R1 (`deepseek-reasoner`)  
**Machine profile:** CPU-only Linux (WSL or native), modest RAM, no GPU assumed

### DeepSeek Reasoning Rules

**If using DeepSeek R1 (reasoning model):**
- Emit a `<think>` reasoning block before generating any non-trivial code
- For database schema changes, caching logic, or AI prompt design — plan all side effects before writing
- When editing multiple files simultaneously, list every file to be changed and the order of operations first

**If using DeepSeek V3 (fast coding model):**
- Skip extended reasoning; go directly to implementation
- Use test output as your spec — write code that satisfies failing assertions
- After every non-trivial change, emit a bash verification block showing exactly which command to run next

### Agent Mission

You are building and maintaining a **privacy-first, offline-capable AI learning platform**. Every decision optimises for:

1. **Correctness** — all 7 features work exactly as documented
2. **Privacy** — local-first data, Ollama preferred over cloud AI at every decision point
3. **Performance** — caching is core infrastructure, not an afterthought
4. **Maintainability** — a solo developer must be able to understand any file in under 5 minutes

---

## 📁 CANONICAL PROJECT STRUCTURE

Maintain this exact layout. Never create files outside this tree without explicit instruction.

```
advanced-study-assistant/
│
├── app.py                        # Flask application — single backend file (primary target)
├── requirements.txt              # Pinned Python dependencies
├── study_assistant.db            # SQLite database — auto-created on first run
├── .env.example                  # Environment variable template — commit this
├── .env                          # Local secrets — NEVER commit
├── setup.sh                      # One-command bootstrap script
│
├── static/
│   ├── index.html                # Single-page app shell — minimal HTML, no logic
│   ├── script.js                 # All frontend JS — ES6+, no bundler (primary target)
│   └── style.css                 # All styles — CSS variables, dark/light, animations
│
├── tests/
│   ├── conftest.py               # Shared fixtures: Flask test client, mock DB, mock Ollama
│   ├── test_explain.py           # /api/explain endpoint tests
│   ├── test_quiz.py              # /api/quiz endpoint tests
│   ├── test_flashcards.py        # /api/flashcards endpoint tests
│   ├── test_study_plan.py        # /api/study-plan endpoint tests
│   ├── test_mind_map.py          # /api/mind-map endpoint tests
│   ├── test_summarize.py         # /api/summarize endpoint tests
│   ├── test_chat.py              # /api/chat endpoint tests
│   ├── test_cache.py             # Cache layer unit tests
│   ├── test_progress.py          # /api/progress GET + POST tests
│   └── test_ollama.py            # Ollama provider unit tests (always mocked)
│
├── AGENTS.md                     # This file — do not modify without updating all sections
├── README.md                     # Human-facing quickstart
└── IMPROVEMENTS.md               # Feature changelog — READ ONLY, do not modify
```

### File Ownership Rules

| File | Ownership |
|---|---|
| `app.py` | Agent — primary backend target |
| `static/script.js` | Agent — primary frontend target |
| `static/style.css` | Agent — primary style target |
| `static/index.html` | Agent — modify only for structural HTML changes |
| `study_assistant.db` | Runtime only — never commit, never read in tests |
| `.env` | Human only — agent writes `.env.example` |
| `IMPROVEMENTS.md` | Human only — never touch |
| `setup.sh` | Agent can update when new deps added |

---

## 🏗️ SYSTEM ARCHITECTURE

### Full Request Lifecycle

```
Browser (index.html + script.js)
        │
        │  POST /api/{endpoint}
        │  Headers: Content-Type: application/json
        │           X-Session-Token: {uuid}
        ▼
Flask Route Handler (app.py)
        │
        ├─► 1. Input Validation (bleach.clean + length checks)
        │         └─ FAIL → 400 JSON error with human message
        │
        ├─► 2. Rate Limit Check (per session-token, 30 req/min)
        │         └─ EXCEEDED → 429 JSON error with retry_after
        │
        ├─► 3. Cache Lookup (SQLite cache table, SHA256 key, 24h TTL)
        │         └─ HIT → return cached JSON with "cached": true flag
        │
        ├─► 4. AI Provider Call
        │         ├─ Ollama local  → POST http://localhost:11434/api/generate
        │         │     └─ DOWN   → OllamaError → 503 JSON error (never 500)
        │         └─ Puter AI     → handled client-side (not via this route)
        │
        ├─► 5. Response Parsing (extract structured JSON from AI text)
        │         └─ PARSE FAIL → retry with stricter prompt, then error
        │
        ├─► 6. Cache Write (SQLite, expires_at = now + 24h)
        │
        ├─► 7. Progress Log (SQLite user_progress table)
        │
        └─► 8. JSON Response → browser
                  {"success": true, "data": {...}, "cached": false, ...}
```

### AI Provider Decision Tree

```python
# Enforced in every AI-calling endpoint:
# 1. If provider == "ollama" AND Ollama is reachable → use Ollama
# 2. If provider == "ollama" AND Ollama is DOWN      → return structured OllamaError (never silently fall back to cloud)
# 3. If provider == "puter"                          → this route is not called; Puter is client-side only
#
# NEVER:
# - Fall back to cloud silently when Ollama is selected
# - Expose raw exception messages to HTTP responses
# - Make blocking calls without timeout
# - Return HTTP 500 — every failure path returns a structured JSON error
```

---

## 🗄️ DATABASE SCHEMA

### Authoritative SQLite Schema

Every table must be created in `db_init()` which is called at Flask app startup, before any route is registered.

```sql
-- Cache: stores AI responses keyed by SHA256(endpoint+params)
CREATE TABLE IF NOT EXISTS cache (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    key        TEXT UNIQUE NOT NULL,
    value      TEXT NOT NULL,               -- JSON string of full AI response payload
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL           -- created_at + CACHE_TTL_HOURS
);

-- User progress: one row per learning activity
CREATE TABLE IF NOT EXISTS user_progress (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    topic        TEXT NOT NULL,
    activity     TEXT NOT NULL,             -- 'explanation'|'quiz'|'flashcard'|'study_plan'|'mind_map'|'summary'|'chat'
    score        REAL,                      -- NULL for non-quiz; 0.0–100.0 for quiz results
    duration     INTEGER,                   -- estimated seconds spent (optional)
    metadata     TEXT,                      -- JSON blob for activity-specific extras
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Study sessions: groups activity into per-browser-session buckets
CREATE TABLE IF NOT EXISTS study_sessions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    session_token  TEXT UNIQUE NOT NULL,    -- UUID sent by browser in X-Session-Token header
    started_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activity_count INTEGER DEFAULT 0
);
```

### Database Rules
- **Always** use parameterised queries — `?` placeholders, never f-strings in SQL
- **Always** call `db_init()` at startup via `with app.app_context(): db_init()`
- Cache key = `hashlib.sha256(json.dumps({"endpoint": e, **sorted_params}).encode()).hexdigest()`
- Expired cache rows are cleaned lazily on read (delete-on-miss), not on write
- In tests, use `DATABASE=":memory:"` — never touch the real `.db` file in tests
- Never expose raw SQLite errors in HTTP responses — catch, log internally, return structured error

---

## 🔌 API ENDPOINT CONTRACTS

Every endpoint follows this exact request/response shape. New endpoints must conform.

### Standard Request Body
```json
{
  "topic":    "string, required for most endpoints",
  "level":    "beginner | intermediate | advanced — optional, default: beginner",
  "provider": "ollama | puter — optional, default: ollama",
  "count":    "integer — optional, endpoint-specific range"
}
```

### Standard Success Response
```json
{
  "success":          true,
  "data":             {},
  "cached":           false,
  "provider":         "ollama",
  "response_time_ms": 1240
}
```

### Standard Error Response
```json
{
  "success":     false,
  "error":       "Human-readable message safe to show in UI",
  "code":        "OLLAMA_UNAVAILABLE | RATE_LIMITED | INVALID_INPUT | PARSE_ERROR | INTERNAL_ERROR",
  "retry_after": 60
}
```

### Endpoint Catalogue — Full Spec

| Route | Method | Input Fields | Output `data` Shape |
|---|---|---|---|
| `/api/explain` | POST | `topic`, `level` | `{explanation, examples[], key_concepts[], analogies[], misconceptions[]}` |
| `/api/quiz` | POST | `topic`, `count` (3–10), `difficulty` | `{questions: [{question, options[], answer, explanation, hint}]}` |
| `/api/flashcards` | POST | `topic`, `count` (5–20) | `{cards: [{front, back, difficulty, color}]}` |
| `/api/study-plan` | POST | `topic`, `days` (1–30), `hours_per_day` (1–8) | `{plan: [{day, tasks[], milestones[], resources[]}]}` |
| `/api/mind-map` | POST | `topic` | `{center, branches: [{label, color, children[]}]}` |
| `/api/summarize` | POST | `notes` (raw text), `format` | `{summary, key_points[], format_used}` |
| `/api/chat` | POST | `message`, `history[]` | `{response, suggestions[]}` |
| `/api/progress` | GET | — | `{stats{}, recent_topics[], activity_breakdown{}, streak_days}` |
| `/api/progress` | POST | `topic`, `activity`, `score?` | `{saved: true}` |
| `/api/ollama/status` | GET | — | `{available: bool, models[], default_model}` |

### Cache Behaviour Per Endpoint

| Endpoint | Cached? | Reason |
|---|---|---|
| `/api/explain` | ✅ Yes | Deterministic output for same topic+level |
| `/api/quiz` | ✅ Yes | Same params → same questions acceptable |
| `/api/flashcards` | ✅ Yes | Same topic → same cards acceptable |
| `/api/study-plan` | ✅ Yes | Stable plans for same inputs |
| `/api/mind-map` | ✅ Yes | Structure is deterministic |
| `/api/summarize` | ✅ Yes | Keyed by hash of the notes text |
| `/api/chat` | ❌ No | Conversational context changes every call |
| `/api/progress` | ❌ No | Must always reflect live DB state |
| `/api/ollama/status` | ❌ No | Real-time health check |

---

## 🤖 OLLAMA INTEGRATION

### Connection & Call Pattern

```python
import os, time, requests
from dataclasses import dataclass

OLLAMA_BASE_URL     = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_DEFAULT_MODEL= os.getenv("OLLAMA_MODEL", "deepseek-r1:7b")
OLLAMA_TIMEOUT      = int(os.getenv("OLLAMA_TIMEOUT", "90"))
OLLAMA_MAX_RETRIES  = 2

class OllamaError(Exception):
    """Raised for all Ollama failures. Message is user-safe."""

def check_ollama() -> tuple[bool, list[str]]:
    """Non-blocking health check. Returns (available, model_list)."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            return True, models
        return False, []
    except Exception:
        return False, []

def call_ollama(prompt: str, model: str = None, max_tokens: int = 1000) -> str:
    """Call Ollama with retry + exponential backoff. Returns raw text."""
    target = model or OLLAMA_DEFAULT_MODEL
    for attempt in range(1, OLLAMA_MAX_RETRIES + 1):
        try:
            r = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": target,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "num_predict": max_tokens, "top_p": 0.9},
                },
                timeout=OLLAMA_TIMEOUT,
            )
            r.raise_for_status()
            return r.json()["response"].strip()
        except requests.Timeout:
            if attempt == OLLAMA_MAX_RETRIES:
                raise OllamaError(f"Ollama timed out after {OLLAMA_TIMEOUT}s. Try a smaller model.")
            time.sleep(attempt * 2)
        except requests.ConnectionError:
            raise OllamaError("Ollama is not running. Start it with: ollama serve")
        except KeyError:
            raise OllamaError("Unexpected response format from Ollama. Check your Ollama version.")
        except Exception as e:
            raise OllamaError(f"Ollama error: {type(e).__name__}")
```

### Model Selection Guide

| RAM Available | Model | Pull Command | Notes |
|---|---|---|---|
| 4 GB | `phi3` | `ollama pull phi3` | Fastest, lightweight |
| 8 GB | `deepseek-r1:7b` | `ollama pull deepseek-r1:7b` | **Recommended default** |
| 16 GB | `deepseek-r1:14b` | `ollama pull deepseek-r1:14b` | Better reasoning |
| 32 GB+ | `deepseek-v2.5` | `ollama pull deepseek-v2.5` | Best quality |

---

## ⚡ CACHING SYSTEM

### Full Cache Implementation

```python
import hashlib, json
from datetime import datetime, timedelta

CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))

def make_cache_key(endpoint: str, params: dict) -> str:
    """Deterministic key. Sorted params ensure key stability regardless of dict ordering."""
    canonical = json.dumps({"endpoint": endpoint, **params}, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()

def cache_get(key: str) -> dict | None:
    """Return cached value or None. Lazily deletes expired entries."""
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
    """Upsert cache entry. Always succeeds silently on write failure (non-critical path)."""
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
        pass  # Cache write failure is non-fatal — log but don't raise
```

### Caching Rules
- Check cache before **every** Ollama call — order is: validate → rate-limit → cache → AI
- Write to cache only on **successful** AI responses — never cache errors or partial responses
- `/api/chat` and `/api/progress` are **never** cached — see table above
- For `/api/summarize`: cache key includes a hash of the raw `notes` text, not just topic
- Agent must never manually invalidate cache — expiry is TTL-only

---

## 🔒 INPUT VALIDATION

### Validation Layer (runs on every endpoint, before cache and AI)

```python
import bleach

MAX_TOPIC_LENGTH   = 200
MAX_NOTES_LENGTH   = 10_000
MAX_MESSAGE_LENGTH = 2_000
VALID_LEVELS       = {"beginner", "intermediate", "advanced"}
VALID_ACTIVITIES   = {"explanation", "quiz", "flashcard", "study_plan", "mind_map", "summary", "chat"}
VALID_FORMATS      = {"bullet", "paragraph", "outline", "cornell"}

def validate_topic(raw: str) -> str:
    if not raw or not isinstance(raw, str):
        raise ValueError("Topic is required.")
    clean = bleach.clean(raw.strip())
    if len(clean) < 2:
        raise ValueError("Topic must be at least 2 characters.")
    if len(clean) > MAX_TOPIC_LENGTH:
        raise ValueError(f"Topic must be under {MAX_TOPIC_LENGTH} characters.")
    return clean

def validate_level(raw: str | None) -> str:
    if not raw:
        return "beginner"
    lvl = raw.lower().strip()
    return lvl if lvl in VALID_LEVELS else "beginner"

def validate_count(raw, min_val: int, max_val: int, default: int) -> int:
    try:
        return max(min_val, min(max_val, int(raw)))
    except (TypeError, ValueError):
        return default

def validate_notes(raw: str) -> str:
    if not raw or not isinstance(raw, str):
        raise ValueError("Notes text is required.")
    if len(raw) > MAX_NOTES_LENGTH:
        raise ValueError(f"Notes must be under {MAX_NOTES_LENGTH} characters.")
    return bleach.clean(raw.strip())
```

### Security Rules
1. **Always** call `bleach.clean()` before injecting any user string into an AI prompt
2. **Always** use `?` parameterised placeholders in every SQL statement
3. **Never** expose Python exception messages in HTTP responses — map to safe user messages
4. **Never** log full conversation history — log only `topic` and `activity` type
5. Rate limiting key is `X-Session-Token` header value, stored in `study_sessions`
6. HTML/JS in topic input must be stripped (bleach), not rejected — silent sanitisation

---

## 🎨 FRONTEND ARCHITECTURE

### JavaScript State & API Pattern (script.js)

```javascript
// ── Global State — single source of truth ──────────────────────────────────
const AppState = {
  currentFeature:      'explain',      // which tab/panel is active
  provider:            'ollama',       // 'ollama' | 'puter'
  theme:               'auto',         // 'light' | 'dark' | 'auto'
  ollamaAvailable:     false,          // updated by /api/ollama/status on load
  conversationHistory: [],             // chat context — never persisted to backend
  sessionToken:        null,           // UUID, set on first load, sent in every request
};

// ── API Call Wrapper — ALL backend calls use this ──────────────────────────
async function apiCall(endpoint, payload = {}) {
  setLoading(true);
  const start = Date.now();
  try {
    const resp = await fetch(`/api/${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Token': AppState.sessionToken,
      },
      body: JSON.stringify({ ...payload, provider: AppState.provider }),
    });
    const data = await resp.json();

    if (!data.success) {
      showToast(data.error, 'error');
      return null;
    }
    if (data.cached) showToast('Loaded from cache ⚡', 'info', 2000);
    return data.data;

  } catch (err) {
    showToast('Network error — check your connection.', 'error');
    return null;
  } finally {
    setLoading(false);
  }
}

// ── Toast System ────────────────────────────────────────────────────────────
// type: 'info' | 'success' | 'error' | 'warning'
// Toasts stack vertically, auto-dismiss after `duration` ms
// Maximum 3 toasts visible simultaneously (oldest removed)
function showToast(message, type = 'info', duration = 4000) { /* ... */ }

// ── Feature Render Functions — one per feature, no shared render logic ─────
function renderExplanation(data)        { /* ... */ }
function renderQuiz(data)               { /* ... */ }
function renderFlashcards(data)         { /* ... */ }
function renderStudyPlan(data)          { /* ... */ }
function renderMindMap(data)            { /* ... */ }
function renderSummary(data)            { /* ... */ }
function renderChatMessage(msg, role)   { /* ... */ }
function renderProgressStats(data)      { /* ... */ }

// ── Flashcard Flip — CSS-only, no JS animation ─────────────────────────────
// HTML structure required for flip animation:
// <div class="flashcard" onclick="this.classList.toggle('flipped')">
//   <div class="flashcard-inner">
//     <div class="flashcard-front">...</div>
//     <div class="flashcard-back">...</div>
//   </div>
// </div>
```

### CSS Design System (style.css)

```css
/* ── Design Tokens — ALL values reference these, never hardcode ── */
:root {
  /* Color palette */
  --c-bg:           #0f1117;
  --c-surface:      #1a1d27;
  --c-surface-2:    #252836;
  --c-border:       #2e3244;
  --c-text:         #e8eaf0;
  --c-text-muted:   #8b92a9;
  --c-accent:       #6c63ff;
  --c-accent-hover: #7c74ff;
  --c-success:      #2ecc71;
  --c-warning:      #f39c12;
  --c-error:        #e74c3c;
  --c-info:         #3498db;

  /* Difficulty — used by flashcards and quiz */
  --c-easy:   #27ae60;
  --c-medium: #f39c12;
  --c-hard:   #e74c3c;

  /* Spacing scale */
  --sp-xs: 4px;   --sp-sm: 8px;   --sp-md: 16px;
  --sp-lg: 24px;  --sp-xl: 40px;  --sp-2xl: 64px;

  /* Border radius */
  --r-sm: 6px;  --r-md: 12px;  --r-lg: 20px;  --r-xl: 32px;

  /* Motion */
  --ease-fast: 150ms ease;
  --ease-base: 250ms ease;
  --ease-slow: 400ms cubic-bezier(0.16, 1, 0.3, 1);

  /* Typography — use distinctive fonts, never Inter/Roboto/Arial */
  --font-body:    'DM Sans', system-ui, sans-serif;
  --font-heading: 'Syne', sans-serif;
  --font-mono:    'JetBrains Mono', monospace;
}

/* Light theme override — applied via JS: document.documentElement.dataset.theme = 'light' */
[data-theme="light"] {
  --c-bg:        #f4f6fb;
  --c-surface:   #ffffff;
  --c-surface-2: #eef0f7;
  --c-border:    #d8dce8;
  --c-text:      #1a1d27;
  --c-text-muted:#6b7080;
}

/* Flashcard flip animation — no JS required */
.flashcard { perspective: 1000px; cursor: pointer; }
.flashcard-inner {
  transition: transform var(--ease-slow);
  transform-style: preserve-3d;
  position: relative;
}
.flashcard.flipped .flashcard-inner { transform: rotateY(180deg); }
.flashcard-front, .flashcard-back {
  backface-visibility: hidden;
  position: absolute; inset: 0;
}
.flashcard-back { transform: rotateY(180deg); }

/* Skeleton loading — no spinners */
.skeleton {
  background: linear-gradient(90deg, var(--c-surface) 25%, var(--c-surface-2) 50%, var(--c-surface) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: var(--r-sm);
}
@keyframes shimmer { to { background-position: -200% 0; } }
```

### Responsive Breakpoints

| Breakpoint | Range | Layout |
|---|---|---|
| Mobile | `< 640px` | Single column, stacked nav, touch-sized buttons (min 44px) |
| Tablet | `640–1024px` | 2-column grid, collapsible sidebar |
| Desktop | `> 1024px` | Multi-column, side-by-side panels, hover effects |

---

## 🧪 TESTING RULES

### Test File Template (copy for every new endpoint)

```python
"""Tests for /api/explain endpoint."""
import pytest, json
from unittest.mock import patch


class TestExplainEndpoint:

    def test_success_returns_correct_schema(self, client, mock_ollama):
        mock_ollama.return_value = json.dumps({
            "explanation": "Python is a programming language.",
            "examples": ["print('hello')"],
            "key_concepts": ["variables", "functions"],
            "analogies": ["like building with LEGO blocks"],
            "misconceptions": ["Python is slow for everything — false"],
        })
        resp = client.post('/api/explain', json={"topic": "Python", "level": "beginner"})
        data = resp.get_json()

        assert resp.status_code == 200
        assert data["success"] is True
        for field in ["explanation", "examples", "key_concepts", "analogies", "misconceptions"]:
            assert field in data["data"]

    def test_missing_topic_returns_400(self, client):
        resp = client.post('/api/explain', json={})
        data = resp.get_json()
        assert resp.status_code == 400
        assert data["success"] is False
        assert data["code"] == "INVALID_INPUT"

    def test_second_identical_request_is_cached(self, client, mock_ollama):
        payload = {"topic": "Recursion", "level": "beginner"}
        client.post('/api/explain', json=payload)          # cache miss
        resp = client.post('/api/explain', json=payload)   # cache hit
        assert resp.get_json()["cached"] is True

    def test_ollama_down_returns_structured_503(self, client):
        with patch('app.call_ollama', side_effect=Exception("Connection refused")):
            resp = client.post('/api/explain', json={"topic": "Python"})
        data = resp.get_json()
        assert resp.status_code == 503
        assert data["success"] is False
        assert "OLLAMA" in data["code"]

    def test_topic_exceeding_max_length_returns_400(self, client):
        resp = client.post('/api/explain', json={"topic": "x" * 500})
        assert resp.status_code == 400

    def test_xss_input_is_sanitised_not_rejected(self, client, mock_ollama):
        mock_ollama.return_value = '{"explanation":"safe","examples":[],"key_concepts":[],"analogies":[],"misconceptions":[]}'
        resp = client.post('/api/explain', json={"topic": "<script>alert(1)</script>Python"})
        assert resp.status_code == 200  # sanitised, not rejected

    def test_invalid_level_defaults_to_beginner(self, client, mock_ollama):
        mock_ollama.return_value = '{"explanation":"ok","examples":[],"key_concepts":[],"analogies":[],"misconceptions":[]}'
        resp = client.post('/api/explain', json={"topic": "Python", "level": "expert"})
        assert resp.status_code == 200  # 'expert' → silently defaults to 'beginner'
```

### conftest.py (required)

```python
"""Shared fixtures for all test modules."""
import pytest
from unittest.mock import patch
from app import create_app   # app.py MUST expose this factory function


@pytest.fixture(scope="session")
def app():
    """Flask app in test mode with in-memory SQLite. Session-scoped for speed."""
    return create_app({
        "TESTING": True,
        "DATABASE": ":memory:",
        "RATE_LIMIT_PER_MINUTE": 99999,   # Disable rate limiting in tests
        "CACHE_TTL_HOURS": 24,
    })

@pytest.fixture
def client(app):
    """Fresh test client per test function."""
    with app.app_context():
        yield app.test_client()

@pytest.fixture
def mock_ollama():
    """Patch Ollama globally — tests NEVER hit real Ollama."""
    with patch('app.call_ollama') as mock:
        mock.return_value = '{"explanation":"test","examples":[],"key_concepts":[],"analogies":[],"misconceptions":[]}'
        yield mock
```

### Coverage Requirements

| Target | Minimum |
|---|---|
| Route handlers (all 10 endpoints) | 85% |
| `cache_get` / `cache_set` / `make_cache_key` | 100% |
| All `validate_*` functions | 100% |
| `call_ollama` (all error paths) | 90% |
| `check_ollama` | 80% |
| `script.js` | Manual smoke test (not measured) |

---

## 🛠️ DEVELOPMENT COMMANDS

### Setup
```bash
python3 --version                      # Must be 3.10+
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pytest==8.2.0 pytest-cov==5.0.0 black==24.4.2 flake8==7.1.0 bleach==6.1.0
cp .env.example .env                   # Then edit .env
```

### Running
```bash
python app.py                           # Dev server on port 5000
PORT=5001 python app.py                 # Custom port
FLASK_DEBUG=1 python app.py             # Hot reload
```

### Code Quality
```bash
black app.py --line-length 100
flake8 app.py --max-line-length 100

# Full pre-commit sequence:
black app.py --line-length 100 && flake8 app.py --max-line-length 100 && pytest tests/ -q
```

### Testing
```bash
pytest tests/ -v                        # All tests, verbose
pytest tests/ -q                        # All tests, quiet (CI mode)
pytest tests/test_explain.py -v         # Single file
pytest -k "cache" -v                    # Tests matching keyword
pytest --cov=app --cov-report=term-missing tests/   # With coverage
OLLAMA_MOCK=true pytest tests/ -q       # Mock mode (no Ollama needed)
```

### Database
```bash
sqlite3 study_assistant.db ".tables"
sqlite3 study_assistant.db "SELECT key, expires_at FROM cache ORDER BY created_at DESC LIMIT 10;"
sqlite3 study_assistant.db "SELECT topic, activity, score FROM user_progress ORDER BY created_at DESC LIMIT 20;"
sqlite3 study_assistant.db "DELETE FROM cache WHERE expires_at < datetime('now');"
rm study_assistant.db && python app.py  # Full reset
```

### Ollama
```bash
ollama serve
ollama list
ollama pull deepseek-r1:7b
ollama run deepseek-r1:7b "Explain recursion in one paragraph"
curl http://localhost:11434/api/tags
curl -s -X POST http://localhost:11434/api/generate \
  -d '{"model":"deepseek-r1:7b","prompt":"Hello","stream":false}' | python3 -m json.tool
```

---

## ⚙️ ENVIRONMENT VARIABLE REFERENCE

```env
# Flask
FLASK_DEBUG=false
PORT=5000
SECRET_KEY=change-this-in-production   # Used for session signing

# Database
DATABASE=study_assistant.db            # Use ':memory:' in tests

# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:7b
OLLAMA_TIMEOUT=90

# Caching
CACHE_TTL_HOURS=24

# Rate limiting
RATE_LIMIT_PER_MINUTE=30

# Logging
LOG_LEVEL=INFO                         # DEBUG | INFO | WARNING | ERROR

# Testing
OLLAMA_MOCK=false                      # Set true to bypass Ollama in tests
```

---

## 🐛 TROUBLESHOOTING REFERENCE

| Symptom | Root Cause | Fix |
|---|---|---|
| `ConnectionRefused` on any `/api/` route | Ollama not running | `ollama serve` |
| `model not found` in error response | Model not pulled | `ollama pull deepseek-r1:7b` |
| Response timeout (>90s) | Model too large for RAM | `OLLAMA_MODEL=phi3` in `.env` |
| `KeyError: 'response'` from Ollama | API format mismatch | Check Ollama version via `curl http://localhost:11434/api/tags` |
| `ImportError` in tests | `create_app()` not exposed | Add `create_app(config=None)` factory to `app.py` |
| Cache never hits | Key mismatch or TTL=0 | Inspect `cache` table; verify `sort_keys=True` in `make_cache_key` |
| Port 5000 conflict (macOS) | AirPlay uses port 5000 | `PORT=5001 python app.py` |
| `database is locked` | Concurrent writes | Add `check_same_thread=False` to `sqlite3.connect()` |
| Dark mode not persisting on reload | Theme not saved | `localStorage.setItem('theme', AppState.theme)` on every change |
| Flashcard flip broken | Missing `perspective` on parent | `.flashcard { perspective: 1000px; }` |
| Chat context lost between messages | `conversationHistory` not passed | Always include full `history[]` array in chat POST payload |

---

## 📏 AGENT DECISION RULES

Apply these in strict priority order when uncertain:

1. **Schema before code** — if a DB table or response shape is not in this file, define it here first, then write the code
2. **Validate before everything** — input validation runs before cache check, before AI call, always
3. **Cache before AI** — check cache before every Ollama call; write to cache after every successful response
4. **Degrade gracefully** — if Ollama is down, return a structured `503` error — never a raw 500, never silence
5. **One config location** — every configurable value lives in `.env` + `os.getenv()`. Never duplicate a constant
6. **Tests cover all error paths** — every endpoint needs: success, missing-input, Ollama-down, and cache-hit tests
7. **Dark mode by default** — verify every new UI component in both themes before marking done
8. **Chat is stateless on the server** — conversation history is sent by the client in every request; the server never stores it

---

## ✅ DONE CHECKLIST

Before marking any task complete:

- [x] **Phase 1 Complete** - Core Infrastructure
  - [x] Flask application with SQLite database setup
  - [极] Database schema (cache, user_progress, study_sessions)
  - [x] Input validation with bleach sanitization
  - [x] Cache system with SHA256 keys and TTL
  - [x] Rate limiting system (30 requests/minute)
  - [x] Ollama integration stubs
  - [x] Error handling with structured JSON responses
  - [x] Health check endpoints
  - [x] Environment configuration
  - [x] Setup script
  - [x] Comprehensive documentation

- [x] **Phase 2 Complete** - Ollama Integration
  - [x] All 7 AI endpoints implemented
  - [x] Comprehensive prompt templates
  - [x] Robust JSON parsing from AI responses
  - [x] Caching for all AI endpoints
  - [x] Progress logging system
  - [x] Ollama error handling
  - [x] Complete testing with mock responses

- [x] **Phase 3 Complete** - Frontend Development
  - [x] Complete HTML structure for all 7 features
  - [x] Comprehensive CSS design system with dark/light themes
  - [x] Vanilla JavaScript implementation with state management
  - [x] Responsive design for mobile, tablet, and desktop
  - [x] Loading states and error handling
  - [x] Theme switching functionality
  - [x] Provider selection (Ollama/Puter)
  - [x] Cache indicators and toast notifications

- [x] `pytest tests/ -q` — all tests pass
- [x] `pytest --cov=app --cov-report=term-missing` — coverage ≥ 85%
- [x] `flake8 app极.py --max-line-length 100` — zero warnings
- [x] `black --check app.py --line-length 100` — already formatted
- [x] Input validated on any new endpoint
- [x] Cache implemented (check + write) on any new AI endpoint
- [x] Progress logged on successful AI response
- [x] Dark mode tested manually at `[data-theme="dark"]`
- [x] Mobile layout verified at 375px viewport
- [ ] Ollama-down scenario tested: stop Ollama, hit endpoint, verify structured error not 500
- [x] No secrets in any `.py` file — `grep -r "password\|api_key\|secret" . --include="*.py"`
- [x] `.env.example` updated if new env vars introduced

---

*Single source of truth for all AI coding agents on this project.*
*Target runtime: opencode + DeepSeek R1 (`deepseek-reasoner`) / DeepSeek V3 (`deepseek-chat`)*
*Project: Advanced AI Study Assistant Pro v2.0*
