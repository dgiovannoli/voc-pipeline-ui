#!/usr/bin/env python3
"""
Production Deployment Script for Supabase-only VOC Pipeline
This script ensures the production environment is properly configured.
"""

import os
import sys
import subprocess
import shutil
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
        print(f"Error output: {e.stderr}")
        return False

def check_supabase_connection():
    """Check if Supabase connection is working"""
    print("🔍 Testing Supabase connection...")
    try:
        # Import and test Supabase connection
        from supabase_database import SupabaseDatabase
        db = SupabaseDatabase()
        
        # Try to get a simple query to test connection
        test_result = db.test_connection()
        if test_result:
            print("✅ Supabase connection successful")
            return True
        else:
            print("❌ Supabase connection failed")
            return False
    except Exception as e:
        print(f"❌ Supabase connection error: {e}")
        return False

def ensure_production_environment():
    """Ensure production environment is properly configured"""
    print("🚀 PRODUCTION DEPLOYMENT - SUPABASE ARCHITECTURE")
    print("=" * 60)
    
    # Get current directory
    current_dir = Path.cwd()
    print(f"📁 Current directory: {current_dir}")
    
    # Check if we're in the right directory
    if not (current_dir / "app.py").exists():
        print("❌ app.py not found in current directory")
        print("💡 Make sure you're in the voc-pipeline-ui directory")
        return False
    
    # Check if all required files exist
    required_files = [
        "app.py",
        "supabase_database.py", 
        "enhanced_stage2_analyzer.py",
        "config/analysis_config.yaml",
        "requirements.txt"
    ]
    
    print("\n🔍 Checking required files...")
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ Required file not found: {file_path}")
            return False
        else:
            print(f"✅ Found: {file_path}")
    
    # Check environment variables
    print("\n🔍 Checking environment variables...")
    required_env_vars = ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_KEY"]
    missing_vars = []
    
    for var in required_env_vars:
        if not os.getenv(var):
            print(f"❌ Environment variable not set: {var}")
            missing_vars.append(var)
        else:
            print(f"✅ Environment variable set: {var}")
    
    if missing_vars:
        print(f"\n⚠️ Missing environment variables: {', '.join(missing_vars)}")
        print("💡 Please set these in your .env file or environment")
        return False
    
    # Check Supabase connection
    if not check_supabase_connection():
        print("❌ Cannot proceed without Supabase connection")
        return False
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️ Virtual environment not detected")
        print("💡 Please activate your virtual environment first:")
        print("   source .venv/bin/activate")
        return False
    
    # Install/update dependencies
    print("\n🔧 Installing/updating dependencies...")
    if not run_command("pip install -r requirements.txt", "Install dependencies"):
        return False
    
    # Kill any existing Streamlit processes
    print("\n🔧 Stopping existing Streamlit processes...")
    run_command("pkill -f streamlit", "Kill existing Streamlit processes")
    
    # Start Streamlit in production mode
    print("\n🚀 Starting Streamlit in production mode...")
    if run_command("streamlit run app.py --server.port 8501 --server.headless true", "Start Streamlit"):
        print("\n✅ PRODUCTION DEPLOYMENT SUCCESSFUL!")
        print("🌐 App is running at: http://localhost:8501")
        print("💡 Use Ctrl+C to stop the server")
        print("\n📊 Production Features:")
        print("   ✅ Supabase-only architecture")
        print("   ✅ Real-time data sync")
        print("   ✅ Scalable cloud database")
        print("   ✅ Enhanced Stage 2 analysis")
        return True
    else:
        print("\n❌ PRODUCTION DEPLOYMENT FAILED!")
        return False

def show_production_status():
    """Show current production status"""
    print("📊 PRODUCTION STATUS")
    print("=" * 50)
    
    # Check if Streamlit is running
    result = subprocess.run("pgrep -f streamlit", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Streamlit is running")
        pids = result.stdout.strip().split('\n')
        for pid in pids:
            if pid:
                print(f"   Process ID: {pid}")
    else:
        print("❌ Streamlit is not running")
    
    # Check Supabase connection
    print("\n🔍 Supabase status:")
    if check_supabase_connection():
        print("✅ Supabase connection healthy")
    else:
        print("❌ Supabase connection failed")
    
    # Check environment variables
    print("\n🔍 Environment variables:")
    env_vars = ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_KEY"]
    for var in env_vars:
        if os.getenv(var):
            print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Not set")

def run_health_check():
    """Run a comprehensive health check"""
    print("🏥 PRODUCTION HEALTH CHECK")
    print("=" * 50)
    
    # Check files
    print("\n📁 File system check:")
    required_files = ["app.py", "supabase_database.py", "enhanced_stage2_analyzer.py"]
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
    
    # Check environment
    print("\n🔍 Environment check:")
    env_vars = ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_KEY"]
    for var in env_vars:
        if os.getenv(var):
            print(f"✅ {var}")
        else:
            print(f"❌ {var}")
    
    # Check Supabase
    print("\n🔍 Supabase check:")
    if check_supabase_connection():
        print("✅ Supabase connection")
    else:
        print("❌ Supabase connection")
    
    # Check Streamlit
    print("\n🔍 Streamlit check:")
    result = subprocess.run("pgrep -f streamlit", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Streamlit running")
    else:
        print("❌ Streamlit not running")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            show_production_status()
        elif sys.argv[1] == "health":
            run_health_check()
        else:
            print("Usage: python deploy_to_production.py [status|health]")
    else:
        ensure_production_environment() 