#!/bin/bash

# Production Startup Script for VOC Pipeline UI
# This script ensures the production environment uses the correct database

echo "🚀 VOC Pipeline UI - Production Startup"
echo "========================================"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 Working directory: $SCRIPT_DIR"

# Change to the script directory
cd "$SCRIPT_DIR"

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found in current directory"
    echo "💡 Make sure you're running this script from the voc-pipeline-ui directory"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not detected"
    echo "💡 Make sure to activate your virtual environment first:"
    echo "   source .venv/bin/activate"
    echo ""
    echo "🔧 Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found"
    exit 1
fi

echo "🔧 Checking database schema..."
if python3 production_fix.py; then
    echo "✅ Database fix completed successfully"
else
    echo "❌ Database fix failed"
    exit 1
fi

echo "🔧 Stopping existing Streamlit processes..."
pkill -f streamlit 2>/dev/null || true

echo "🚀 Starting Streamlit in production mode..."
echo "🌐 App will be available at: http://localhost:8501"
echo "💡 Press Ctrl+C to stop the server"
echo ""

# Start Streamlit with production settings
streamlit run app.py --server.port 8501 --server.headless true 