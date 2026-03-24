#!/bin/bash

# Study Assistant Deployment Script
set -e

echo "🚀 Deploying Advanced AI Study Assistant Pro"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data

# Build and start containers
echo "📦 Building and starting containers..."
docker-compose up -d --build

echo "✅ Deployment complete!"
echo "🌐 Application available at: http://localhost:5000"
echo "📊 Health check: curl http://localhost:5000/api/health"
echo "🤖 Ollama available at: http://localhost:11434"

# Show container status
echo ""
echo "📊 Container status:"
docker-compose ps