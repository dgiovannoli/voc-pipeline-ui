#!/usr/bin/env python3

import pandas as pd
from supabase_database import SupabaseDatabase

def debug_mapping():
    """Debug the interviewee name to interview_id mapping"""
    
    # Initialize database connection
    db = SupabaseDatabase()
    
    # Read the CSV file
    csv_path = "Context/stage1_data_responses_rows (2).csv"
    df = pd.read_csv(csv_path)
    
    # Get interview metadata
    metadata_response = db.supabase.table('interview_metadata').select('*').eq('client_id', 'Rev').execute()
    metadata_df = pd.DataFrame(metadata_response.data)
    
    print("📋 Interview Metadata Names:")
    for _, row in metadata_df.iterrows():
        interviewee_name = row.get('interviewee_name', '').strip()
        interview_id = row.get('interview_id', '').strip()
        print(f"  '{interviewee_name}' -> '{interview_id}'")
    
    print(f"\n📊 CSV Sample Response IDs:")
    for i, row in df.head(10).iterrows():
        response_id = row.get('response_id', '')
        interviewee_name = row.get('interviewee_name', '').strip()
        print(f"  Row {i}: response_id='{response_id}', interviewee_name='{interviewee_name}'")
        
        # Try to extract name from response_id
        if response_id and 'Unknown_' in response_id:
            parts = response_id.split('_')
            if len(parts) >= 3:
                extracted_name = parts[1] + ' ' + parts[2]
                print(f"    Extracted name: '{extracted_name}'")
    
    # Check for exact matches
    print(f"\n🔍 Checking for exact matches...")
    metadata_names = set(row.get('interviewee_name', '').strip() for _, row in metadata_df.iterrows())
    
    csv_names = set()
    for _, row in df.iterrows():
        response_id = row.get('response_id', '')
        interviewee_name = row.get('interviewee_name', '').strip()
        
        # Extract from response_id
        if response_id and 'Unknown_' in response_id:
            parts = response_id.split('_')
            if len(parts) >= 3:
                extracted_name = parts[1] + ' ' + parts[2]
                csv_names.add(extracted_name)
        
        # Add from interviewee_name field
        if interviewee_name:
            csv_names.add(interviewee_name)
    
    print(f"📋 CSV Names: {sorted(csv_names)}")
    print(f"📋 Metadata Names: {sorted(metadata_names)}")
    
    # Find matches
    matches = csv_names.intersection(metadata_names)
    print(f"\n✅ Exact matches: {matches}")
    
    # Find partial matches
    partial_matches = []
    for csv_name in csv_names:
        for metadata_name in metadata_names:
            if csv_name.lower() in metadata_name.lower() or metadata_name.lower() in csv_name.lower():
                partial_matches.append((csv_name, metadata_name))
    
    print(f"\n🔍 Partial matches:")
    for csv_name, metadata_name in partial_matches:
        print(f"  '{csv_name}' ~ '{metadata_name}'")

if __name__ == "__main__":
    debug_mapping() 