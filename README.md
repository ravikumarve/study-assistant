# Advanced AI Study Assistant Pro

<div align="center">

```
  ___    _   _   _   _    _   _   ___   ___    _   _   ___   _   _  
 / _ \  | | | | | | | |  | | | | | __| | _ )  | | | | |_ _| | \ | | 
| | | | | |_| | | |_| |  | |_| | | _|  | _ \  | |_| |  | |  |  \| | 
| |_| | |  _  | |  _  |  |  _  | | |_  | | | | |  _  |  | |  | |\  | 
 \___/  |_| |_| |_| |_|  |_| |_| |___| |_| |_| |_| |_| |___| |_| \_| 
                                                                     
```

**Advanced AI Study Assistant Pro - Privacy-First Learning Platform**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.3%2B-green)
![Ollama](https://img.shields.io/badge/Ollama-Local%20AI-orange)
![License](https://img.shields.io/badge/License-MIT-brightgreen)
![Privacy](https://img.shields.io/badge/Privacy-First-critical)

### 🎨 Visual Showcase

```
    ██████████████████████████████████████
    ██                                ██
    ██        ADVANCED AI             ██
    ██        STUDY ASSISTANT         ██
    ██            PRO                 ██
    ██                                ██
    ██  🧠 + 📚 + 🤖 = 🎯            ██
    ██                                ██
    ██████████████████████████████████████
    ██  Privacy-First Learning Platform ██
    ██████████████████████████████████████
```

### 🎨 Logo Concept

```
    ╔══════════════════════════════╗
    ║         🧠                   ║
    ║      +  📚  =  🎯            ║
    ║         🤖                   ║
    ║                              ║
    ║   ADVANCED AI STUDY ASSISTANT║
    ╚══════════════════════════════╝
```

A privacy-first, offline-capable AI learning platform built with Flask and vanilla JavaScript. This study assistant provides intelligent learning tools while keeping your data local and secure.

[🚀 Quick Start](#-quick-start) • [✨ Features](#-features) • [🛡️ Privacy](#️-privacy-first) • [📊 Implementation Status](#-implementation-status)

</div>

## ✨ Features

| Feature | Description | Status |
|---------|-------------|---------|
| 🤖 AI Explanations | Detailed explanations with examples and analogies | ✅ Complete |
| 📝 Interactive Quizzes | Customized quizzes with multiple difficulty levels | ✅ Complete |
| 🎴 Smart Flashcards | Intelligent flashcards with spaced repetition | ✅ Complete |
| 📅 Study Plans | Personalized study schedules and timelines | ✅ Complete |
| 🧠 Mind Maps | **Visual concept mapping with Mermaid.js diagrams** | ✅ Enhanced |
| 📋 Note Summarization | Automatic summarization of study notes | ✅ Complete |
| 💬 AI Chat | Conversational learning assistant | ✅ Complete |
| 📊 Progress Tracking | Detailed learning analytics and statistics | ✅ Complete |
| 🔒 Privacy First | Local AI processing, no data leaves your device | ✅ Complete |
| 🐳 Docker Support | Containerized deployment with Docker | ✅ Complete |
| 📋 Copy to Clipboard | **One-click copy for all AI-generated content** | ✅ New |
| 🎯 Confidence Scores | **AI confidence ratings for content accuracy** | ✅ New |
| ⏱️ Study Time Estimates | **Estimated learning time for each topic** | ✅ New |
| 🎨 Glassmorphism UI | **Modern glass design with visual effects** | ✅ New |

## 📸 Screenshot Gallery

*(Screenshots will be added after application deployment)*

| Feature | Description |
|---------|-------------|
| **Dashboard Overview** | Main interface showing all 7 learning tools |
| **AI Explanations** | Detailed topic explanations with examples and analogies |
| **Interactive Quiz** | Multiple-choice questions with instant feedback |
| **Smart Flashcards** | Digital flashcards with flip animation |
| **Study Plans** | Personalized learning schedules and timelines |
| **Dark/Light Theme** | Theme switching functionality |
| **Mobile Responsive** | Optimized for mobile devices |

## 🎥 Quick Demo

```bash
# See it in action (requires Ollama)
git clone https://github.com/ravikumarve/study-assistant.git
cd study-assistant
./deploy.sh
# Open http://localhost:5000
```

## 🎬 Live Demo

```
Initializing Study Assistant... [██████████] 100%

=== MAIN MENU ===
1. 🤖 AI Explanations     4. 📅 Study Plans
2. ❓ Interactive Quiz    5. 🧠 Mind Maps  
3. 🎴 Smart Flashcards    6. 📋 Note Summarizer
7. 💬 AI Chat

Selecting: 🤖 AI Explanations...
Topic: Machine Learning
Generating... [██████████] 100%

Displaying explanation with examples...
Switching to dark theme... 🌙
Mobile view activated... 📱
```

**Demo Features Shown:**
- 🚀 Application startup
- 🧠 AI-powered explanations  
- ❓ Interactive quizzes
- 🎴 Smart flashcards
- 🌙 Dark/light theme switching
- 📱 Mobile responsiveness

*Actual screen recording GIF will be added here*

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

### ✅ Phase 2 Complete - Ollama Integration
- All 7 AI endpoints implemented
- Comprehensive prompt templates
- Robust JSON parsing from AI responses
- Caching for all AI endpoints
- Progress logging system
- Ollama error handling
- Complete testing with mock responses

### ✅ Phase 3 Complete - Frontend Development
- Complete HTML structure for all 7 features
- Comprehensive CSS design system with dark/light themes
- Vanilla JavaScript implementation with state management
- Responsive design for mobile, tablet, and desktop
- Loading states and error handling
- Theme switching functionality
- Provider selection (Ollama/Puter)
- Cache indicators and toast notifications
- Documentation completion

### ✅ Phase 4 Complete - Production Deployment
- Docker containerization with health checks
- Production deployment scripts
- Performance optimizations (database indexes)
- Advanced monitoring and logging
- Production environment configuration
- Comprehensive testing verification

### ✅ Phase 5 Complete - Enhanced User Experience
- Glassmorphism UI design implementation
- Copy to clipboard functionality for all AI content
- Mermaid.js integration for visual mind maps
- Enhanced AI responses with confidence scores and study time estimates
- Metadata badges for confidence, time, and complexity levels
- Comprehensive CSS styling for new UI components

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
   Navigate to `http://localhost:8001`

### 🐳 Docker Deployment (Alternative)

1. **Build and start with Docker Compose**
   ```bash
   ./deploy.sh
   ```

2. **Or manually with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Monitor the deployment**
   ```bash
   ./monitor.sh
   ```

### Getting Started with Phase 1

The core infrastructure is now complete. You can test the following endpoints:

```bash
# Health check
curl http://localhost:8001/api/health

# Ollama status
curl http://localhost:8001/api/ollama/status

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
- **Glassmorphism design effects**
- **One-click copy to clipboard**
- **Visual mind maps with Mermaid.js**
- **Confidence score badges**
- **Study time estimates**

### API Endpoints

All features are available via REST API:

```bash
# Get explanation
curl -X POST http://localhost:8001/api/explain \
  -H "Content-Type: application/json" \
  -d '{"topic": "Python programming", "level": "beginner"}'

# Generate quiz
curl -极X POST http://localhost:8001/api/quiz \
  -H "Content-Type: application/json" \
  -d '{"topic": "Calculus", "count": 5, "difficulty": "medium"}'

# Create flashcards
curl -X POST http://localhost:8001/api/flashcards \
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
   PORT=8003 python app.py
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

## 🐳 Docker Deployment

The application supports Docker deployment for production environments:

### Quick Deployment
```bash
./deploy.sh
```

### Manual Deployment
```bash
docker-compose up -d
```

### Monitoring
```bash
./monitor.sh
```

### Configuration
- Uses `docker-compose.yml` for multi-container setup
- Includes Ollama service for local AI processing
- Health checks and automatic restarts
- Volume mounts for persistent data

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