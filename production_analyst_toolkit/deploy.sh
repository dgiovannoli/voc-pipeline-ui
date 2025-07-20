#!/bin/bash

# Production Analyst Toolkit Deployment Script
echo "🎯 Production Analyst Toolkit Deployment"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "generate_enhanced_analyst_toolkit.py" ]; then
    echo "❌ Error: Please run this script from the production_analyst_toolkit directory"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Generate a fresh report
echo "🎯 Generating fresh analyst report..."
python generate_enhanced_analyst_toolkit.py

# Start Streamlit app
echo "🚀 Starting Streamlit app..."
echo "📱 Access the app at: http://localhost:8503"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

streamlit run streamlit_app.py --server.headless true --server.port 8503 