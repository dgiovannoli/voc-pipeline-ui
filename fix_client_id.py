#!/usr/bin/env python3
"""
Fix client_id issue in Streamlit app
"""

import streamlit as st
from supabase_database import SupabaseDatabase

def fix_client_id():
    """Set the correct client_id in Streamlit session state"""
    
    print("🔧 Fixing client_id in Streamlit session state")
    print("=" * 50)
    
    # Check current session state
    current_client_id = st.session_state.get('client_id', 'not_set')
    print(f"Current client_id in session: {current_client_id}")
    
    # Set the correct client_id
    st.session_state.client_id = 'Rev'
    print(f"✅ Set client_id to 'Rev'")
    
    # Verify the fix
    new_client_id = st.session_state.get('client_id', 'not_set')
    print(f"New client_id in session: {new_client_id}")
    
    # Test database access
    try:
        db = SupabaseDatabase()
        responses = db.get_stage1_data_responses(client_id='Rev')
        print(f"📊 Database responses for client 'Rev': {len(responses)}")
        
        if len(responses) > 0:
            print(f"✅ Successfully retrieved {len(responses)} responses")
            print(f"📋 Sample response:")
            sample = responses.iloc[0]
            print(f"  ID: {sample.get('response_id', 'N/A')}")
            print(f"  Company: {sample.get('company', 'N/A')}")
            print(f"  Interviewee: {sample.get('interviewee_name', 'N/A')}")
            print(f"  Subject: {sample.get('subject', 'N/A')}")
        else:
            print("❌ No responses found for client 'Rev'")
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")

if __name__ == "__main__":
    fix_client_id() 