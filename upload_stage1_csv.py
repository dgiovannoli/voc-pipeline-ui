#!/usr/bin/env python3

import pandas as pd
import os
import sys
from supabase_database import SupabaseDatabase
from datetime import datetime

def upload_stage1_csv():
    """Upload Stage 1 CSV data to database with correct client_id"""
    
    # Initialize database connection
    db = SupabaseDatabase()
    
    # Read the CSV file
    csv_path = "Context/stage1_data_responses_rows (3).csv"
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return False
    
    print(f"📊 Reading CSV file: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"📋 Found {len(df)} rows in CSV")
    
    # Check if data already exists for this client
    client_id = "Rev"
    print(f"🔍 Checking for existing data for client: {client_id}")
    
    try:
        existing_response = db.supabase.table('stage1_data_responses').select('count').eq('client_id', client_id).execute()
        existing_count = existing_response.data[0]['count'] if existing_response.data else 0
        print(f"📊 Found {existing_count} existing records for client {client_id}")
        
        if existing_count > 0:
            print("⚠️ Data already exists for this client. Skipping upload.")
            return True
            
    except Exception as e:
        print(f"❌ Error checking existing data: {e}")
        return False
    
    # Upload data
    print(f"🚀 Uploading {len(df)} records to database...")
    saved_count = 0
    
    for index, row in df.iterrows():
        try:
            response_data = {
                'response_id': row.get('response_id', ''),
                'verbatim_response': row.get('verbatim_response', ''),
                'subject': row.get('subject', ''),
                'question': row.get('question', ''),
                'deal_status': row.get('deal_status', 'closed_won'),
                'company': row.get('company', ''),
                'interviewee_name': row.get('interviewee_name', ''),
                'interview_date': row.get('interview_date', '2024-01-01'),
                'file_source': 'stage1_processing',
                'client_id': client_id,
                'processing_status': 'pending',
                'source_file': row.get('source_file', ''),
                'chunk_info': row.get('chunk_info', '{}'),
                'embedding': row.get('embedding', ''),
                'interview_id': row.get('interview_id', ''),
                'date_of_interview': row.get('date_of_interview', ''),
                'client_name': row.get('client_name', ''),
                'industry': row.get('industry', ''),
                'segment': row.get('segment', '')
            }
            
            if db.save_core_response(response_data):
                saved_count += 1
                
            if (index + 1) % 50 == 0:
                print(f"📊 Progress: {index + 1}/{len(df)} records processed")
                
        except Exception as e:
            print(f"❌ Error saving row {index}: {e}")
            continue
    
    print(f"✅ Successfully uploaded {saved_count}/{len(df)} records to database")
    
    # Verify upload
    try:
        verify_response = db.supabase.table('stage1_data_responses').select('count').eq('client_id', client_id).execute()
        final_count = verify_response.data[0]['count'] if verify_response.data else 0
        print(f"📊 Verification: {final_count} total records now in database for client {client_id}")
    except Exception as e:
        print(f"❌ Error verifying upload: {e}")
    
    return saved_count > 0

if __name__ == "__main__":
    success = upload_stage1_csv()
    if success:
        print("🎉 Upload completed successfully!")
    else:
        print("❌ Upload failed!")
        sys.exit(1) 