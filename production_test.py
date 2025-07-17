#!/usr/bin/env python3
"""
Production Testing Script
Comprehensive testing for production deployment issues
"""

import os
import sys
import logging
import traceback
from dotenv import load_dotenv
import openai
import pandas as pd

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment_variables():
    """Test all required environment variables"""
    print("🔍 Testing Environment Variables...")
    
    required_vars = {
        'OPENAI_API_KEY': 'OpenAI API Key',
        'SUPABASE_URL': 'Supabase URL',
        'SUPABASE_ANON_KEY': 'Supabase Anonymous Key'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append(f"❌ {description} ({var})")
        else:
            print(f"✅ {description}: Set")
    
    if missing_vars:
        print("❌ Missing Environment Variables:")
        for var in missing_vars:
            print(f"  {var}")
        return False
    
    print("✅ All environment variables are set")
    return True

def test_openai_connection():
    """Test OpenAI API connection"""
    print("\n🤖 Testing OpenAI Connection...")
    
    try:
        # Test basic OpenAI connection
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        print("✅ OpenAI API connection successful")
        return True
    except Exception as e:
        print(f"❌ OpenAI API connection failed: {e}")
        return False

def test_supabase_connection():
    """Test Supabase database connection"""
    print("\n🗄️ Testing Supabase Connection...")
    
    try:
        from supabase_database import SupabaseDatabase
        db = SupabaseDatabase()
        
        # Test basic query
        result = db.supabase.table('stage1_data_responses').select('count').limit(1).execute()
        print("✅ Supabase connection successful")
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

def test_database_schema():
    """Test database schema and table access"""
    print("\n📊 Testing Database Schema...")
    
    try:
        from supabase_database import SupabaseDatabase
        db = SupabaseDatabase()
        
        # Test all required tables
        tables = [
            'stage1_data_responses',
            'stage2_response_labeling', 
            'stage3_findings',
            'stage4_themes',
            'interview_metadata'
        ]
        
        for table in tables:
            try:
                result = db.supabase.table(table).select('count').limit(1).execute()
                print(f"✅ Table '{table}': Accessible")
            except Exception as e:
                print(f"❌ Table '{table}': {e}")
                return False
        
        print("✅ All database tables accessible")
        return True
    except Exception as e:
        print(f"❌ Database schema test failed: {e}")
        return False

def test_imports():
    """Test all critical module imports"""
    print("\n📦 Testing Module Imports...")
    
    modules = [
        'stage3_findings_analyzer_enhanced',
        'stage4_theme_analyzer', 
        'supabase_database',
        'openai',
        'pandas',
        'numpy',
        'sklearn.feature_extraction.text',
        'sklearn.metrics.pairwise',
        'sklearn.cluster'
    ]
    
    failed_imports = []
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"❌ Failed imports: {failed_imports}")
        return False
    
    print("✅ All modules imported successfully")
    return True

def test_stage3_analyzer():
    """Test Stage 3 analyzer functionality"""
    print("\n🔍 Testing Stage 3 Analyzer...")
    
    try:
        from stage3_findings_analyzer_enhanced import EnhancedStage3FindingsAnalyzer
        
        # Test analyzer initialization
        analyzer = EnhancedStage3FindingsAnalyzer('Rev')
        print("✅ Stage 3 analyzer initialized")
        
        # Test prompt loading
        prompt = analyzer._load_buried_wins_prompt()
        if prompt and len(prompt) > 100:
            print("✅ Buried Wins prompt loaded")
        else:
            print("❌ Buried Wins prompt failed to load")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Stage 3 analyzer test failed: {e}")
        traceback.print_exc()
        return False

def test_stage4_analyzer():
    """Test Stage 4 analyzer functionality"""
    print("\n🎯 Testing Stage 4 Analyzer...")
    
    try:
        from stage4_theme_analyzer import Stage4ThemeAnalyzer
        
        # Test analyzer initialization
        analyzer = Stage4ThemeAnalyzer()
        print("✅ Stage 4 analyzer initialized")
        
        return True
    except Exception as e:
        print(f"❌ Stage 4 analyzer test failed: {e}")
        traceback.print_exc()
        return False

def test_file_permissions():
    """Test file system permissions"""
    print("\n📁 Testing File Permissions...")
    
    try:
        # Test writing to current directory
        test_file = 'production_test_temp.txt'
        with open(test_file, 'w') as f:
            f.write('test')
        
        # Test reading
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Clean up
        os.remove(test_file)
        
        print("✅ File read/write permissions OK")
        return True
    except Exception as e:
        print(f"❌ File permissions test failed: {e}")
        return False

def test_memory_usage():
    """Test memory usage and limits"""
    print("\n💾 Testing Memory Usage...")
    
    try:
        import psutil
        memory = psutil.virtual_memory()
        print(f"✅ Available memory: {memory.available / (1024**3):.1f} GB")
        
        if memory.available < 1 * (1024**3):  # Less than 1GB
            print("⚠️ Low memory available")
            return False
        
        return True
    except ImportError:
        print("⚠️ psutil not available, skipping memory test")
        return True
    except Exception as e:
        print(f"❌ Memory test failed: {e}")
        return False

def test_network_connectivity():
    """Test network connectivity to external services"""
    print("\n🌐 Testing Network Connectivity...")
    
    try:
        import requests
        
        # Test OpenAI API endpoint
        response = requests.get('https://api.openai.com/v1/models', timeout=10)
        if response.status_code == 401:  # Expected for unauthorized
            print("✅ OpenAI API reachable")
        else:
            print(f"⚠️ OpenAI API response: {response.status_code}")
        
        # Test Supabase endpoint
        supabase_url = os.getenv('SUPABASE_URL')
        if supabase_url:
            response = requests.get(f"{supabase_url}/rest/v1/", timeout=10)
            print(f"✅ Supabase API reachable")
        
        return True
    except Exception as e:
        print(f"❌ Network connectivity test failed: {e}")
        return False

def run_comprehensive_test():
    """Run all production tests"""
    print("🚀 Starting Production Deployment Tests\n")
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("OpenAI Connection", test_openai_connection),
        ("Supabase Connection", test_supabase_connection),
        ("Database Schema", test_database_schema),
        ("Module Imports", test_imports),
        ("Stage 3 Analyzer", test_stage3_analyzer),
        ("Stage 4 Analyzer", test_stage4_analyzer),
        ("File Permissions", test_file_permissions),
        ("Memory Usage", test_memory_usage),
        ("Network Connectivity", test_network_connectivity)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 PRODUCTION TEST SUMMARY")
    print("="*50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📈 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Production deployment should work.")
    else:
        print("⚠️ Some tests failed. Review the issues above before deploying.")
        
        # Specific recommendations
        if any("OpenAI" in name and not result for name, result in results):
            print("\n🔧 OpenAI Issues - Check:")
            print("  - API key is valid and has credits")
            print("  - API key is properly set in environment")
            print("  - Network connectivity to OpenAI")
        
        if any("Supabase" in name and not result for name, result in results):
            print("\n🔧 Supabase Issues - Check:")
            print("  - Database URL and key are correct")
            print("  - Database is online and accessible")
            print("  - Tables exist and have proper permissions")
    
    return failed == 0

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1) 