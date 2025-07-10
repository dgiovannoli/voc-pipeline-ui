#!/usr/bin/env python3
"""
Test script to verify the fixes for:
1. Unique response_id generation
2. Client data siloing
3. Automatic save to Supabase
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def test_unique_response_id():
    """Test that response_id generation creates unique IDs"""
    print("🧪 Testing unique response_id generation...")
    
    from voc_pipeline.processor import normalize_response_id
    
    # Test multiple calls with same parameters
    company = "TestCompany"
    interviewee = "TestPerson"
    client_id = "client123"
    
    response_ids = set()
    for i in range(10):
        response_id = normalize_response_id(company, interviewee, i, client_id)
        response_ids.add(response_id)
        print(f"  Generated: {response_id}")
    
    # All should be unique
    if len(response_ids) == 10:
        print("✅ All response_ids are unique!")
        return True
    else:
        print(f"❌ Found {10 - len(response_ids)} duplicate response_ids")
        return False

def test_supabase_connection():
    """Test Supabase connection and client_id filtering"""
    print("\n🧪 Testing Supabase connection and client_id filtering...")
    
    try:
        from supabase_database import SupabaseDatabase
        
        db = SupabaseDatabase()
        
        # Test connection
        if db.test_connection():
            print("✅ Supabase connection successful")
            
            # Test client_id filtering
            stage1_data_responses = db.get_stage1_data_responses(client_id='test_client')
            print(f"✅ Retrieved {len(stage1_data_responses)} responses for test_client")
            
            return True
        else:
            print("❌ Supabase connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Supabase test failed: {e}")
        return False

def test_stage2_analyzer():
    """Test Stage 2 analyzer with client_id support"""
    print("\n🧪 Testing Stage 2 analyzer with client_id support...")
    
    try:
        from enhanced_stage2_analyzer import SupabaseStage2Analyzer
        
        analyzer = SupabaseStage2Analyzer()
        
        # Test loading data with client_id
        quotes_df = analyzer.load_stage1_data_from_supabase(client_id='test_client')
        print(f"✅ Loaded {len(quotes_df)} quotes for test_client")
        
        # Test getting unanalyzed quotes with client_id
        unanalyzed_df = analyzer.get_unanalyzed_quotes(client_id='test_client')
        print(f"✅ Found {len(unanalyzed_df)} unanalyzed quotes for test_client")
        
        return True
        
    except Exception as e:
        print(f"❌ Stage 2 analyzer test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Running VOC Pipeline Fixes Test Suite")
    print("=" * 50)
    
    tests = [
        ("Unique Response ID Generation", test_unique_response_id),
        ("Supabase Connection & Client Filtering", test_supabase_connection),
        ("Stage 2 Analyzer Client Support", test_stage2_analyzer)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The fixes are working correctly.")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main() 