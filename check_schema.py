#!/usr/bin/env python3

from supabase_database import SupabaseDatabase

def check_schema():
    """Check the schema of the stage1_data_responses table"""
    
    # Initialize database connection
    db = SupabaseDatabase()
    
    # Get a sample record to see the structure
    print("🔍 Checking stage1_data_responses table schema...")
    try:
        response = db.supabase.table('stage1_data_responses').select('*').limit(1).execute()
        if response.data:
            record = response.data[0]
            print(f"📋 Sample record keys: {list(record.keys())}")
            print(f"📋 Sample record: {record}")
        else:
            print("❌ No records found in stage1_data_responses table")
    except Exception as e:
        print(f"❌ Error checking schema: {e}")
    
    # Also check interview_metadata table
    print("\n🔍 Checking interview_metadata table schema...")
    try:
        response = db.supabase.table('interview_metadata').select('*').limit(1).execute()
        if response.data:
            record = response.data[0]
            print(f"📋 Sample record keys: {list(record.keys())}")
            print(f"📋 Sample record: {record}")
        else:
            print("❌ No records found in interview_metadata table")
    except Exception as e:
        print(f"❌ Error checking schema: {e}")

if __name__ == "__main__":
    check_schema() 