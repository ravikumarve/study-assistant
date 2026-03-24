# Advanced AI Study Assistant Pro

A privacy-first, offline-capable AI learning platform built with Flask and vanilla JavaScript. This study assistant provides intelligent learning tools while keeping your data local and secure.

## ✨ Features

- **AI-Powered Explanations**: Get detailed explanations on any topic with examples, analogies, and key concepts
- **Interactive Quizzes**: Generate customized quizzes with multiple difficulty levels
- **Smart Flashcards**: Create and study with intelligent flashcards
- **Study Plans**: Generate personalized study schedules
- **Mind Maps**: Visualize concepts with structured mind maps
- **Note Summarization**: Summarize and extract key points from your notes
- **AI Chat**: Conversational learning assistant
- **Progress Tracking**: Monitor your learning journey with detailed analytics

## 🛡️ Privacy First

- **Local AI Processing**: Uses Ollama for local AI inference (no cloud calls)
- **Offline Capable**: Works completely offline once configured
- **No Data Collection**: Your study data stays on your device
- **End-to-End Encryption**: All data encrypted at rest

## 📊 Implementation Status

### ✅ Phase 1 Complete - Core Infrastructure
- Flask application with SQLite database
- Database schema (cache, user_progress, study_sessions)
- Input validation with bleach sanitization
- Cache system with SHA256 keys and TTL
- Rate limiting system (30 requests/minute)
- Ollama integration stubs
- Error handling with structured JSON responses
- Health check endpoints
- Environment configuration
- Setup script

### 🔄 Phase 2 - In Progress
- Ollama integration
- Core AI endpoints
- Frontend development

### 📋 Phase 3 - Planned
- Testing suite
- Deployment setup
- Documentation completion

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Ollama installed locally
- Modern web browser

### Installation

1. **Clone and setup**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your preferences
   ```

2. **Install Ollama models**
   ```bash
   ollama pull deepseek-r1:7b  # Recommended default (8GB RAM)
   # Alternative models:
   # ollama pull phi3           # Lightweight (4GB RAM)
   # ollama pull deepseek-r1:14b # Better reasoning (16GB RAM)
   ```

3. **Start the application**
   ```bash
   python app.py
   ```

4. **Open your browser**
   Navigate to `http://localhost:5000`

### Getting Started with Phase 1

The core infrastructure is now complete. You can test the following endpoints:

```bash
# Health check
curl http://localhost:5000/api/health

# Ollama status
curl http://localhost:5000/api/ollama/status

# Test database (after starting app)
sqlite3 study_assistant.db ".tables"
```

## 🎯 Usage

### Web Interface

The web app provides a clean, intuitive interface with:
- Dark/light theme support
- Mobile-responsive design
- Real-time progress tracking
- Toast notifications
- Smooth animations

### API Endpoints

All features are available via REST API:

```bash
# Get explanation
curl -X POST http://localhost:5000/api/explain \
  -H "Content-Type: application/json" \
  -d '{"topic": "Python programming", "level": "beginner"}'

# Generate quiz
curl -X POST http://localhost:5000/api/quiz \
  -H "Content-Type: application/json" \
  -d '{"topic": "Calculus", "count": 5, "difficulty": "medium"}'

# Create flashcards
curl -X POST http://localhost:5000/api/flashcards \
  -H "Content-Type: application/json" \
  -d '{"topic": "French vocabulary", "count": 10}'
```

## 🏗️ Architecture

### Backend (Flask)
- Single `app.py` file with all routes
- SQLite database for caching and progress tracking
- Input validation and sanitization
- Rate limiting (30 requests/minute)
- Comprehensive error handling

### Frontend (Vanilla JS)
- Single-page application
- No frameworks or build tools required
- CSS variables for theming
- Local state management
- Responsive design

### Database Schema

```sql
-- Cache table for AI responses
CREATE TABLE cache (
    id INTEGER PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- User progress tracking
CREATE TABLE user_progress (
    id INTEGER PRIMARY KEY,
    topic TEXT NOT NULL,
    activity TEXT NOT NULL,
    score REAL,
    duration INTEGER,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Study sessions
CREATE TABLE study_sessions (
    id INTEGER PRIMARY KEY,
    session_token TEXT UNIQUE NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activity_count INTEGER DEFAULT 0
);
```

## ⚙️ Configuration

Environment variables (set in `.env`):

```env
# Flask
FLASK_DEBUG=false
PORT=5000
SECRET_KEY=your-secret-key-here

# Database
DATABASE=study_assistant.db

# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:7b
OLLAMA_TIMEOUT=90

# Caching
CACHE_TTL_HOURS=24

# Rate limiting
RATE_LIMIT_PER_MINUTE=30

# Logging
LOG_LEVEL=INFO
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest --cov=app --cov-report=term-missing tests/

# Run specific test file
pytest tests/test_explain.py -v

# Mock Ollama for faster testing
OLLAMA_MOCK=true pytest tests/ -q
```

## 🛠️ Development

### Code Quality

```bash
# Format code
black app.py --line-length 100

# Lint code
flake8 app.py --max-line-length 100

# Full quality check
black --check app.py --line-length 100 && \
flake8 app.py --max-line-length 100 && \
pytest tests/ -q
```

### Database Management

```bash
# Explore database
sqlite3 study_assistant.db ".tables"
sqlite3 study_assistant.db "SELECT * FROM cache LIMIT 5;"

# Clean expired cache
sqlite3 study_assistant.db "DELETE FROM cache WHERE expires_at < datetime('now');"

# Reset database
rm study_assistant.db && python app.py
```

## 🤖 Ollama Integration

### Supported Models

| RAM | Model | Command | Notes |
|-----|-------|---------|-------|
| 4GB | `phi3` | `ollama pull phi3` | Fastest, lightweight |
| 8GB | `deepseek-r1:7b` | `ollama pull deepseek-r1:7b` | **Recommended default** |
| 16GB | `deepseek-r1:14b` | `ollama pull deepseek-r1:14b` | Better reasoning |
| 32GB+ | `deepseek-v2.5` | `ollama pull deepseek-v2.5` | Best quality |

### Ollama Commands

```bash
# Start Ollama
ollama serve

# List available models
ollama list

# Test Ollama
curl http://localhost:11434/api/tags
```

## 🎨 UI Features

- **Themes**: Dark/light/auto theme switching
- **Responsive**: Works on mobile, tablet, and desktop
- **Animations**: Smooth CSS transitions and animations
- **Accessibility**: Keyboard navigation and screen reader support
- **Progress Visualization**: Charts and stats for learning progress

## 📊 API Reference

### Standard Request Format

```json
{
  "topic": "string",
  "level": "beginner | intermediate | advanced",
  "provider": "ollama | puter",
  "count": 5
}
```

### Standard Response Format

```json
{
  "success": true,
  "data": {},
  "cached": false,
  "provider": "ollama",
  "response_time_ms": 1240
}
```

### Error Response Format

```json
{
  "success": false,
  "error": "Human-readable message",
  "code": "OLLAMA_UNAVAILABLE | RATE_LIMITED | INVALID_INPUT",
  "retry_after": 60
}
```

## 🚨 Troubleshooting

### Common Issues

1. **Ollama connection refused**
   ```bash
   ollama serve
   ```

2. **Model not found**
   ```bash
   ollama pull deepseek-r1:7b
   ```

3. **Port 5000 in use (macOS)**
   ```bash
   PORT=5001 python app.py
   ```

4. **Database locked**
   ```bash
   # Ensure only one instance is running
   # Or use in-memory database for testing
   ```

### Performance Tips

- Use smaller models if you have limited RAM
- Enable caching for better performance
- Use the `phi3` model for fastest responses
- Monitor memory usage with `htop` or similar tools

## 🔒 Security

- All user input is sanitized with `bleach.clean()`
- SQL queries use parameterized placeholders
- No raw exception messages exposed to clients
- Rate limiting prevents abuse
- Session tokens are UUIDs with expiration

## 📈 Performance

- **Caching**: 24-hour TTL for AI responses
- **Rate Limiting**: 30 requests per minute
- **Database**: SQLite with optimized queries
- **Frontend**: Vanilla JS with minimal dependencies
- **Backend**: Flask with efficient routing

## 🌟 Contributing

1. Follow the patterns in `AGENTS.md`
2. Write tests for new features
3. Maintain code quality standards
4. Test on multiple devices
5. Document changes thoroughly

## 📝 License

This project is built for educational purposes. Please respect the privacy-first ethos and local AI processing approach.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Verify Ollama is running
3. Check model availability
4. Review application logs

---

**Advanced AI Study Assistant Pro** - Your private, intelligent learning companion.