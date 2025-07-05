#!/usr/bin/env python3
"""
Environment Setup Script for VOC Pipeline Production
"""

import os
from pathlib import Path

def create_env_file():
    """Create .env file with required environment variables"""
    
    env_file = Path(".env")
    
    if env_file.exists():
        print("📄 .env file already exists")
        return True
    
    print("🔧 Creating .env file...")
    
    # Get current environment variables
    openai_key = os.getenv("OPENAI_API_KEY", "")
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_ANON_KEY", "")
    
    # Create .env content
    env_content = f"""# VOC Pipeline Environment Variables
# Copy your actual values here

# OpenAI API Key (required)
OPENAI_API_KEY={openai_key}

# Supabase Configuration (required for production)
SUPABASE_URL={supabase_url}
SUPABASE_ANON_KEY={supabase_key}

# Optional: Database configuration
# DATABASE_URL=your_database_url_here
"""
    
    # Write .env file
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file")
    print("💡 Please edit .env file with your actual credentials")
    return True

def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Checking environment configuration...")
    
    # Check .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check required variables
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API Key",
        "SUPABASE_URL": "Supabase Project URL", 
        "SUPABASE_ANON_KEY": "Supabase Anonymous Key"
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append(f"{var} ({description})")
        else:
            print(f"✅ {description}: Set")
    
    if missing_vars:
        print(f"\n❌ Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Please set these in your .env file")
        return False
    
    print("✅ Environment configuration complete")
    return True

def show_setup_instructions():
    """Show setup instructions"""
    print("🚀 VOC Pipeline Production Setup")
    print("=" * 50)
    print()
    print("📋 To complete production setup, you need:")
    print()
    print("1. OpenAI API Key")
    print("   - Get from: https://platform.openai.com/api-keys")
    print("   - Add to .env file as OPENAI_API_KEY")
    print()
    print("2. Supabase Project")
    print("   - Create at: https://supabase.com")
    print("   - Get Project URL and Anonymous Key")
    print("   - Add to .env file as SUPABASE_URL and SUPABASE_ANON_KEY")
    print()
    print("3. Run database migration")
    print("   - python migrate_to_supabase.py")
    print()
    print("4. Deploy to production")
    print("   - python deploy_production.py")
    print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "check":
            check_environment()
        elif sys.argv[1] == "create":
            create_env_file()
        else:
            print("Usage: python setup_environment.py [check|create]")
    else:
        show_setup_instructions()
        create_env_file()
        check_environment() 