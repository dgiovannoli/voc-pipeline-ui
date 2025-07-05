#!/bin/bash

# Production Startup Script for Supabase-only VOC Pipeline UI
# This script ensures the production environment is properly configured

echo "🚀 VOC Pipeline UI - Production Startup (Supabase)"
echo "=================================================="

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

# Check environment variables
echo "🔍 Checking environment variables..."
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY not set"
    echo "💡 Please set your OpenAI API key in the environment"
    exit 1
fi

if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
    echo "❌ Error: Supabase credentials not set"
    echo "💡 Please set SUPABASE_URL and SUPABASE_KEY in the environment"
    exit 1
fi

echo "✅ Environment variables configured"

# Install/update dependencies
echo "🔧 Installing/updating dependencies..."
pip install -r requirements.txt

# Test Supabase connection
echo "🔍 Testing Supabase connection..."
python3 -c "
from supabase_database import SupabaseDatabase
try:
    db = SupabaseDatabase()
    if db.test_connection():
        print('✅ Supabase connection successful')
    else:
        print('❌ Supabase connection failed')
        exit(1)
except Exception as e:
    print(f'❌ Supabase connection error: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Supabase connection failed"
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