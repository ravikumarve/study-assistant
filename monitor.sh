#!/bin/bash

# Monitoring script for StudyMind

echo "📊 StudyMind Monitoring"
echo "=============================="

# Check if containers are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Containers are running"
else
    echo "❌ Containers are not running"
    exit 1
fi

# Health check
echo ""
echo "🏥 Health Check:"
if curl -s http://localhost:5000/api/health > /dev/null; then
    echo "✅ Application is healthy"
else
    echo "❌ Application health check failed"
fi

# Ollama status
echo ""
echo "🤖 Ollama Status:"
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama is running"
    models=$(curl -s http://localhost:11434/api/tags | jq -r '.models[].name' 2>/dev/null || echo "No models found")
    echo "   Available models: $models"
else
    echo "❌ Ollama is not responding"
fi

# Database status
echo ""
echo "💾 Database Status:"
if [ -f "data/studymind.db" ]; then
    size=$(du -h "data/studymind.db" | cut -f1)
    echo "✅ Database file exists ($size)"
else
    echo "❌ Database file not found"
fi

# Show logs
echo ""
echo "📋 Recent logs:"
docker-compose logs --tail=10 studymind