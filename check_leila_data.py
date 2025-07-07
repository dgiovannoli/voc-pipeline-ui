#!/usr/bin/env python3
"""
Check all Leila's data in the database
"""

from supabase_database import SupabaseDatabase
import pandas as pd

def check_leila_data():
    """Check all data related to Leila Vaez-Iravani"""
    
    print("🔍 Checking Leila's data in database")
    print("=" * 50)
    
    try:
        db = SupabaseDatabase()
        
        # Get all responses for client 'Rev'
        responses = db.get_core_responses(client_id='Rev')
        print(f"📊 Total responses for client 'Rev': {len(responses)}")
        
        # Filter for Leila specifically
        leila_responses = responses[responses['interviewee_name'].str.contains('Leila', case=False, na=False)]
        print(f"👤 Leila responses: {len(leila_responses)}")
        
        if len(leila_responses) > 0:
            print(f"\n📋 Leila's responses:")
            for i, (_, row) in enumerate(leila_responses.iterrows(), 1):
                print(f"\n{i}. {row.get('response_id', 'N/A')}")
                print(f"   Subject: {row.get('subject', 'N/A')}")
                print(f"   Question: {row.get('question', 'N/A')}")
                print(f"   Verbatim preview: {row.get('verbatim_response', 'N/A')[:100]}...")
        
        # Check quote analysis
        quote_analysis = db.get_quote_analysis(client_id='Rev')
        print(f"\n📈 Quote analysis records: {len(quote_analysis)}")
        
        # Check enhanced findings
        findings = db.get_enhanced_findings(client_id='Rev')
        print(f"🔍 Enhanced findings: {len(findings)}")
        
        # Check themes
        themes = db.get_themes(client_id='Rev')
        print(f"🎯 Themes: {len(themes)}")
        
        # Summary
        print(f"\n📊 Summary for client 'Rev':")
        print(f"  Core responses: {len(responses)}")
        print(f"  Quote analyses: {len(quote_analysis)}")
        print(f"  Enhanced findings: {len(findings)}")
        print(f"  Themes: {len(themes)}")
        
        if len(leila_responses) > 0:
            print(f"\n✅ Leila's data is present in the database!")
            print(f"   You should see {len(leila_responses)} quotes from Leila in the UI")
            print(f"   Make sure to set Client ID to 'Rev' in the Streamlit sidebar")
        else:
            print(f"\n❌ No Leila responses found")
            
    except Exception as e:
        print(f"❌ Error checking data: {e}")

if __name__ == "__main__":
    check_leila_data() 