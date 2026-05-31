#!/bin/bash

# Gym Workout RAG - Application Startup Script

echo "============================================"
echo "  Gym Workout RAG - Application Launcher"
echo "============================================"
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python -m venv venv && ./venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Install Flask dependencies if needed
echo "📦 Checking Flask dependencies..."
./venv/bin/pip install -q Flask requests

echo ""
echo "🚀 Starting application..."
echo ""
echo "📍 Flask Frontend: http://localhost:7500"
echo "📍 FastAPI Backend: http://localhost:8000"
echo ""
echo "⏳ Please wait 10-30 seconds for both servers to initialize"
echo "💡 Press Ctrl+C to stop both servers"
echo ""
echo "============================================"
echo ""

# Run the Flask app (which will auto-start FastAPI)
./venv/bin/python flask/app.py

# Made with Bob
