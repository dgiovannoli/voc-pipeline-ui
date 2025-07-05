#!/usr/bin/env python3
"""
Production Deployment Script for Supabase-only VOC Pipeline
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        return False

def check_environment():
    """Check production environment"""
    print("🔍 Checking production environment...")
    
    # Check required files
    required_files = ["app.py", "supabase_database.py", "enhanced_stage2_analyzer.py"]
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ Required file not found: {file_path}")
            return False
        print(f"✅ Found: {file_path}")
    
    # Check environment variables
    required_vars = ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_ANON_KEY"]
    for var in required_vars:
        if not os.getenv(var):
            print(f"❌ Environment variable not set: {var}")
            return False
        print(f"✅ Environment variable set: {var}")
    
    return True

def test_supabase():
    """Test Supabase connection"""
    print("🔍 Testing Supabase connection...")
    try:
        from supabase_database import SupabaseDatabase
        db = SupabaseDatabase()
        if db.test_connection():
            print("✅ Supabase connection successful")
            return True
        else:
            print("❌ Supabase connection failed")
            return False
    except Exception as e:
        print(f"❌ Supabase connection error: {e}")
        return False

def deploy():
    """Deploy to production"""
    print("🚀 PRODUCTION DEPLOYMENT - SUPABASE ARCHITECTURE")
    print("=" * 60)
    
    # Check environment
    if not check_environment():
        print("❌ Environment check failed")
        return False
    
    # Test Supabase
    if not test_supabase():
        print("❌ Supabase test failed")
        return False
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Install dependencies"):
        return False
    
    # Stop existing processes
    run_command("pkill -f streamlit", "Stop existing Streamlit processes")
    
    # Start production server
    print("🚀 Starting production server...")
    print("🌐 App will be available at: http://localhost:8501")
    print("💡 Press Ctrl+C to stop the server")
    
    # Start Streamlit
    subprocess.run("streamlit run app.py --server.port 8501 --server.headless true", shell=True)

if __name__ == "__main__":
    deploy() 