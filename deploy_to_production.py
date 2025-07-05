#!/usr/bin/env python3
"""
Production Deployment Script
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

def ensure_production_environment():
    """Ensure production environment is properly configured"""
    print("🚀 PRODUCTION DEPLOYMENT")
    print("=" * 50)
    
    # Get current directory
    current_dir = Path.cwd()
    print(f"📁 Current directory: {current_dir}")
    
    # Check if we're in the right directory
    if not (current_dir / "app.py").exists():
        print("❌ app.py not found in current directory")
        print("💡 Make sure you're in the voc-pipeline-ui directory")
        return False
    
    # Check if database exists and is correct
    print("\n🔍 Checking database...")
    if not run_command("python production_fix.py", "Database schema check"):
        return False
    
    # Check if all required files exist
    required_files = [
        "app.py",
        "database.py", 
        "enhanced_stage2_analyzer.py",
        "voc_pipeline.db",
        "config/analysis_config.yaml"
    ]
    
    print("\n🔍 Checking required files...")
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ Required file not found: {file_path}")
            return False
        else:
            print(f"✅ Found: {file_path}")
    
    # Check environment variables
    print("\n🔍 Checking environment...")
    required_env_vars = ["OPENAI_API_KEY"]
    for var in required_env_vars:
        if not os.getenv(var):
            print(f"⚠️ Environment variable not set: {var}")
        else:
            print(f"✅ Environment variable set: {var}")
    
    # Kill any existing Streamlit processes
    print("\n🔧 Stopping existing Streamlit processes...")
    run_command("pkill -f streamlit", "Kill existing Streamlit processes")
    
    # Start Streamlit in production mode
    print("\n🚀 Starting Streamlit in production mode...")
    if run_command("streamlit run app.py --server.port 8501 --server.headless true", "Start Streamlit"):
        print("\n✅ PRODUCTION DEPLOYMENT SUCCESSFUL!")
        print("🌐 App is running at: http://localhost:8501")
        print("💡 Use Ctrl+C to stop the server")
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
    
    # Check database status
    print("\n📊 Database status:")
    run_command("python production_fix.py info", "Database info")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            show_production_status()
        elif sys.argv[1] == "fix":
            run_command("python production_fix.py", "Fix database")
        else:
            print("Usage: python deploy_to_production.py [status|fix]")
    else:
        ensure_production_environment() 