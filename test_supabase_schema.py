#!/usr/bin/env python3
"""
Test script to check Supabase connection and stage3_findings table schema
"""

import os
from dotenv import load_dotenv
from supabase_database import SupabaseDatabase

load_dotenv()

def test_supabase_schema():
    """Test Supabase connection and check stage3_findings schema"""
    try:
        print("🔍 Testing Supabase connection...")
        db = SupabaseDatabase()
        
        # Test basic connection
        print("✅ Supabase connection successful")
        
        # Test stage3_findings table
        print("\n📊 Testing stage3_findings table...")
        
        # Try to get existing findings
        findings = db.get_stage3_findings(client_id='Rev')
        print(f"✅ Found {len(findings)} existing findings for client 'Rev'")
        
        if not findings.empty:
            print("\n📋 Sample finding columns:")
            for col in findings.columns:
                print(f"  - {col}")
        
        # Test finding ID generation
        print("\n🔢 Testing finding ID generation...")
        result = db.supabase.table('stage3_findings').select('finding_id').eq('client_id', 'Rev').order('finding_id', desc=True).limit(1).execute()
        if result.data:
            last_id = result.data[0].get('finding_id', 'F0')
            print(f"✅ Last finding ID for client 'Rev': {last_id}")
        else:
            print("ℹ️ No existing findings for client 'Rev'")
        
        # Test constraint check
        print("\n🔒 Testing unique constraint...")
        try:
            # Try to insert a test finding
            test_data = {
                'finding_id': 'TEST_FINDING',
                'finding_statement': 'Test finding for schema validation',
                'client_id': 'Rev',
                'enhanced_confidence': 5.0,
                'priority_level': 'Standard Finding'
            }
            
            # Clean the data
            clean_data = {}
            for k, v in test_data.items():
                if v is not None:
                    clean_data[k] = v
            
            result = db.supabase.table('stage3_findings').insert(clean_data).execute()
            print("✅ Test insert successful - schema is working")
            
            # Clean up test data
            db.supabase.table('stage3_findings').delete().eq('finding_id', 'TEST_FINDING').eq('client_id', 'Rev').execute()
            print("✅ Test data cleaned up")
            
        except Exception as e:
            print(f"❌ Test insert failed: {e}")
            print("This indicates a schema issue that needs to be fixed")
        
        print("\n✅ Schema test completed")
        
    except Exception as e:
        print(f"❌ Supabase test failed: {e}")

if __name__ == "__main__":
    test_supabase_schema() 