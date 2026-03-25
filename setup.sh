#!/bin/bash

# StudyMind Setup Script

echo "Setting up StudyMind..."

# Check Python version
python3 --version
if [ $? -ne 0 ]; then
    echo "Error: Python 3.10+ is required"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Copy environment file
echo "Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Please edit .env file with your configuration"
else
    echo ".env file already exists, skipping"
fi

# Check if Ollama is installed
echo "Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo "Ollama is installed"
    echo "You may want to run: ollama pull deepseek-r1:7b"
else
    echo "Warning: Ollama is not installed"
    echo "Visit https://ollama.ai/ to install Ollama"
fi

echo ""
echo "Setup complete!"
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Install Ollama models: ollama pull deepseek-r1:7b"
echo "3. Start the application: python app.py"
echo "4. Open http://localhost:5000 in your browser"