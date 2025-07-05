#!/usr/bin/env python3
"""
Quick Setup Script for Supabase Configuration
"""

import os
from pathlib import Path

def setup_supabase():
    """Interactive Supabase setup"""
    print("🚀 Supabase Setup for VOC Pipeline")
    print("=" * 40)
    print()
    print("📋 You need to create a Supabase project and get your credentials.")
    print()
    print("1. Go to https://supabase.com")
    print("2. Sign up/login and create a new project")
    print("3. Wait for setup to complete (2-3 minutes)")
    print("4. Go to Settings → API in your dashboard")
    print("5. Copy your Project URL and Anon Key")
    print()
    
    # Get credentials from user
    supabase_url = input("Enter your Supabase Project URL: ").strip()
    supabase_key = input("Enter your Supabase Anon Key: ").strip()
    
    if not supabase_url or not supabase_key:
        print("❌ Credentials not provided")
        return False
    
    # Update .env file
    env_file = Path(".env")
    if env_file.exists():
        # Read current content
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Replace placeholder values
        content = content.replace("your_supabase_project_url_here", supabase_url)
        content = content.replace("your_supabase_anon_key_here", supabase_key)
        
        # Write back
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ Updated .env file with Supabase credentials")
        return True
    else:
        print("❌ .env file not found")
        return False

def test_supabase_connection():
    """Test Supabase connection"""
    print("🔍 Testing Supabase connection...")
    
    try:
        from supabase_database import SupabaseDatabase
        db = SupabaseDatabase()
        if db.test_connection():
            print("✅ Supabase connection successful!")
            return True
        else:
            print("❌ Supabase connection failed")
            return False
    except Exception as e:
        print(f"❌ Supabase connection error: {e}")
        return False

if __name__ == "__main__":
    if setup_supabase():
        print("\n🔍 Testing connection...")
        if test_supabase_connection():
            print("\n✅ Setup complete! You can now deploy to production.")
            print("💡 Run: python deploy_production.py")
        else:
            print("\n❌ Connection test failed. Please check your credentials.")
    else:
        print("\n❌ Setup failed. Please try again.") 