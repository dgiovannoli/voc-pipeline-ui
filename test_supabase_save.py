#!/usr/bin/env python3
"""
Test script to check Supabase save functionality
"""

import pandas as pd
from supabase_database import SupabaseDatabase
import os
from dotenv import load_dotenv

load_dotenv()

def test_supabase_save():
    """Test saving the processed data to Supabase"""
    
    print("🧪 Testing Supabase save functionality")
    print("=" * 50)
    
    # Check if we have the test output
    if not os.path.exists("test_output.csv"):
        print("❌ test_output.csv not found. Run the processing first.")
        return
    
    # Load the data
    df = pd.read_csv("test_output.csv")
    print(f"📊 Loaded {len(df)} responses from test_output.csv")
    
    # Initialize database
    try:
        db = SupabaseDatabase()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Test saving with client_id 'Rev'
    client_id = 'Rev'
    saved_count = 0
    
    print(f"\n💾 Saving {len(df)} responses to Supabase with client_id: {client_id}")
    
    for _, row in df.iterrows():
        response_data = {
            'response_id': row.get('response_id', ''),
            'verbatim_response': row.get('verbatim_response', ''),
            'subject': row.get('subject', ''),
            'question': row.get('question', ''),
            'deal_status': row.get('deal_status', 'closed_won'),
            'company': row.get('company', ''),
            'interviewee_name': row.get('interviewee_name', ''),
            'interview_date': row.get('date_of_interview', '2024-01-01'),
            'file_source': 'test_processing',
            'client_id': client_id
        }
        
        try:
            if db.save_core_response(response_data):
                saved_count += 1
                print(f"✅ Saved: {response_data['response_id']}")
            else:
                print(f"❌ Failed to save: {response_data['response_id']}")
        except Exception as e:
            print(f"❌ Error saving {response_data['response_id']}: {e}")
    
    print(f"\n📈 Save Results:")
    print(f"  Total responses: {len(df)}")
    print(f"  Successfully saved: {saved_count}")
    print(f"  Failed: {len(df) - saved_count}")
    
    # Verify the data is in the database
    print(f"\n🔍 Verifying data in database...")
    try:
        all_responses = db.get_core_responses(client_id=client_id)
        print(f"📊 Total responses in database for client '{client_id}': {len(all_responses)}")
        
        if len(all_responses) > 0:
            print(f"📋 Sample response from database:")
            sample = all_responses.iloc[0]
            print(f"  ID: {sample.get('response_id', 'N/A')}")
            print(f"  Company: {sample.get('company', 'N/A')}")
            print(f"  Interviewee: {sample.get('interviewee_name', 'N/A')}")
            print(f"  Subject: {sample.get('subject', 'N/A')}")
        
        # Check for Leila specifically
        leila_responses = [r for r in all_responses.to_dict('records') if 'Leila' in str(r.get('interviewee_name', ''))]
        print(f"👤 Leila responses in database: {len(leila_responses)}")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")

if __name__ == "__main__":
    test_supabase_save() 