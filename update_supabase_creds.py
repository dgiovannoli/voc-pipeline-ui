#!/usr/bin/env python3
"""
Update Supabase Credentials Script
"""

import os
from pathlib import Path

def update_supabase_credentials():
    """Update Supabase credentials in .env file"""
    
    print("🔧 Supabase Credentials Update")
    print("=" * 40)
    print()
    print("📋 You need your Supabase Project URL and Anon Key.")
    print("   Get these from: https://supabase.com → Your Project → Settings → API")
    print()
    
    # Get credentials from user
    supabase_url = input("Enter your Supabase Project URL: ").strip()
    supabase_key = input("Enter your Supabase Anon Key: ").strip()
    
    if not supabase_url or not supabase_key:
        print("❌ Credentials not provided")
        return False
    
    # Read current .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
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

def test_connection():
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
    if update_supabase_credentials():
        print("\n🔍 Testing connection...")
        if test_connection():
            print("\n✅ Setup complete! You can now deploy to production.")
            print("💡 Run: python deploy_production.py")
        else:
            print("\n❌ Connection test failed. Please check your credentials.")
    else:
        print("\n❌ Update failed. Please try again.") 