#!/usr/bin/env python3

from supabase_database import SupabaseDatabase

def test_stage1_access():
    """Test access to Stage 1 data with client_id 'Rev'"""
    
    # Initialize database connection
    db = SupabaseDatabase()
    
    print("🔍 Testing Stage 1 data access...")
    
    # Test with client_id "Rev"
    print("\n📊 Testing with client_id 'Rev':")
    try:
        stage1_data = db.get_stage1_data_responses(client_id='Rev')
        print(f"✅ Found {len(stage1_data)} records for client 'Rev'")
        
        if len(stage1_data) > 0:
            print(f"📋 Sample record:")
            sample = stage1_data.iloc[0]
            print(f"  - response_id: {sample.get('response_id', 'N/A')}")
            print(f"  - interviewee_name: {sample.get('interviewee_name', 'N/A')}")
            print(f"  - company: {sample.get('company', 'N/A')}")
            print(f"  - client_id: {sample.get('client_id', 'N/A')}")
        else:
            print("❌ No records found for client 'Rev'")
            
    except Exception as e:
        print(f"❌ Error accessing data for client 'Rev': {e}")
    
    # Test with client_id "default" for comparison
    print("\n📊 Testing with client_id 'default':")
    try:
        stage1_data_default = db.get_stage1_data_responses(client_id='default')
        print(f"✅ Found {len(stage1_data_default)} records for client 'default'")
    except Exception as e:
        print(f"❌ Error accessing data for client 'default': {e}")
    
    # Test without specifying client_id (should default to 'default')
    print("\n📊 Testing without specifying client_id:")
    try:
        stage1_data_no_id = db.get_stage1_data_responses()
        print(f"✅ Found {len(stage1_data_no_id)} records (default client_id)")
    except Exception as e:
        print(f"❌ Error accessing data without client_id: {e}")

if __name__ == "__main__":
    test_stage1_access() 