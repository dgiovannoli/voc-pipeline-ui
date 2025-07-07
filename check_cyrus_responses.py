#!/usr/bin/env python3

import pandas as pd
from supabase_database import SupabaseDatabase

def check_cyrus_responses():
    db = SupabaseDatabase()
    df = db.get_core_responses(client_id='Rev')
    
    print(f"Total responses in database: {len(df)}")
    
    # Find Cyrus Nazarian responses
    cyrus_responses = df[df['interviewee_name'].str.contains('Cyrus', case=False, na=False)]
    print(f"\nCyrus Nazarian responses found: {len(cyrus_responses)}")
    
    print("\n" + "="*80)
    print("CYRUS NAZARIAN RESPONSES EXTRACTED:")
    print("="*80)
    
    for idx, row in cyrus_responses.iterrows():
        print(f"\nResponse ID: {row['response_id']}")
        print(f"Subject: {row['subject']}")
        print(f"Question: {row['question']}")
        print(f"Response (first 300 chars): {row['verbatim_response'][:300]}...")
        print("-" * 60)
    
    # Also check for any responses with "Altair" in company name
    altair_responses = df[df['company'].str.contains('Altair', case=False, na=False)]
    print(f"\nAltair Law responses found: {len(altair_responses)}")
    
    if len(altair_responses) != len(cyrus_responses):
        print("Note: Company name filtering shows different results than interviewee name filtering")

if __name__ == "__main__":
    check_cyrus_responses() 