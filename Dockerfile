FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Create data directory for SQLite
RUN mkdir -p /data && chown appuser:appuser /data

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Environment variables
ENV FLASK_DEBUG=false
ENV PORT=5000
ENV DATABASE=/data/study_assistant.db
ENV OLLAMA_URL=http://host.docker.internal:11434
ENV OLLAMA_MODEL=deepseek-r1:7b
ENV OLLAMA_TIMEOUT=90
ENV CACHE_TTL_HOURS=24
ENV RATE_LIMIT_PER_MINUTE=30
ENV LOG_LEVEL=INFO

# Run the application
CMD ["python", "app.py"]