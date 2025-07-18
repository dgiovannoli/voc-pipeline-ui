#!/usr/bin/env python3

import pandas as pd
import os
import sys
import re
from supabase_database import SupabaseDatabase
from datetime import datetime

def extract_interview_id_from_file(file_path):
    """Extract interview ID from the top of a transcript file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read first few lines to find interview ID
            first_lines = []
            for i in range(10):  # Check first 10 lines
                line = f.readline().strip()
                if line:
                    first_lines.append(line)
            
            # Look for interview ID patterns
            for line in first_lines:
                # Pattern: IVW-XXXXX (Rev format)
                match = re.search(r'IVW-\d+', line)
                if match:
                    return match.group(0)
            
            return None
    except Exception as e:
        print(f"❌ Error reading file {file_path}: {e}")
        return None

def fix_stage1_with_metadata():
    """Fix Stage 1 data by using interview ID as primary key and metadata as source of truth"""
    
    # Initialize database connection
    db = SupabaseDatabase()
    
    print("🔍 Step 1: Getting interview metadata (source of truth)...")
    try:
        metadata_response = db.supabase.table('interview_metadata').select('*').eq('client_id', 'Rev').execute()
        metadata_df = pd.DataFrame(metadata_response.data)
        print(f"📋 Found {len(metadata_df)} interview metadata records")
        
        # Create mapping from interview_id to metadata
        metadata_map = {}
        for _, row in metadata_df.iterrows():
            interview_id = row.get('interview_id', '').strip()
            if interview_id:
                metadata_map[interview_id] = {
                    'interviewee_name': row.get('interviewee_name', '').strip(),
                    'company': row.get('company', '').strip(),
                    'deal_status': row.get('deal_status', '').strip(),
                    'date_of_interview': row.get('date_of_interview', '').strip()
                }
        
        print(f"📋 Created mapping for {len(metadata_map)} interview IDs")
        
    except Exception as e:
        print(f"❌ Error getting metadata: {e}")
        return False
    
    print("\n🔍 Step 2: Getting Stage 1 data...")
    try:
        stage1_response = db.supabase.table('stage1_data_responses').select('*').eq('client_id', 'Rev').execute()
        stage1_df = pd.DataFrame(stage1_response.data)
        print(f"📊 Found {len(stage1_df)} Stage 1 records")
        
        if len(stage1_df) == 0:
            print("❌ No Stage 1 data found for client Rev")
            return False
            
    except Exception as e:
        print(f"❌ Error getting Stage 1 data: {e}")
        return False
    
    print("\n🔍 Step 3: Extracting interview IDs from transcript files...")
    # Get unique interviewee names from Stage 1 data
    unique_interviewees = stage1_df['interviewee_name'].unique()
    print(f"📋 Found {len(unique_interviewees)} unique interviewees in Stage 1 data")
    
    # Map interviewee names to interview IDs by checking transcript files
    interviewee_to_interview_id = {}
    Context_dir = "Context"
    
    for interviewee in unique_interviewees:
        if pd.isna(interviewee) or not interviewee:
            continue
            
        # Look for transcript file
        transcript_file = None
        for filename in os.listdir(Context_dir):
            if filename.endswith('.txt') and interviewee.lower() in filename.lower():
                transcript_file = os.path.join(Context_dir, filename)
                break
        
        if transcript_file:
            interview_id = extract_interview_id_from_file(transcript_file)
            if interview_id:
                interviewee_to_interview_id[interviewee] = interview_id
                print(f"✅ Mapped '{interviewee}' -> {interview_id}")
            else:
                print(f"❌ Could not extract interview ID from {transcript_file}")
        else:
            print(f"❌ No transcript file found for '{interviewee}'")
    
    print(f"\n📋 Successfully mapped {len(interviewee_to_interview_id)} interviewees to interview IDs")
    
    print("\n🔍 Step 4: Updating Stage 1 data with metadata...")
    updated_count = 0
    errors = []
    
    for _, row in stage1_df.iterrows():
        response_id = row['response_id']
        interviewee_name = row.get('interviewee_name', '')
        
        if pd.isna(interviewee_name) or not interviewee_name:
            continue
        
        # Get interview ID for this interviewee
        interview_id = interviewee_to_interview_id.get(interviewee_name)
        
        if interview_id and interview_id in metadata_map:
            # Get metadata for this interview ID
            metadata = metadata_map[interview_id]
            
            # Update the record with metadata information
            update_data = {
                'interview_id': interview_id,
                'interviewee_name': metadata['interviewee_name'],  # Use metadata name
                'company': metadata['company'],
                'deal_status': metadata['deal_status'],
                'date_of_interview': metadata['date_of_interview']
            }
            
            try:
                db.supabase.table('stage1_data_responses').update(update_data).eq('response_id', response_id).execute()
                updated_count += 1
                print(f"✅ Updated record {response_id} with interview_id {interview_id}")
            except Exception as e:
                errors.append(f"Error updating record {response_id}: {e}")
        else:
            if interview_id:
                print(f"❌ Interview ID {interview_id} not found in metadata for '{interviewee_name}'")
            else:
                print(f"❌ No interview ID found for '{interviewee_name}'")
    
    print(f"\n📊 Summary:")
    print(f"✅ Successfully updated {updated_count} records")
    print(f"❌ {len(errors)} errors occurred")
    
    if errors:
        print(f"\n❌ Errors:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"  {error}")
    
    print("\n🔍 Step 5: Verifying updates...")
    try:
        verification_response = db.supabase.table('stage1_data_responses').select('*').eq('client_id', 'Rev').not_.is_('interview_id', 'null').execute()
        verified_records = len(verification_response.data)
        print(f"📊 Verification: {verified_records} records now have interview_id mapping")
        
        if verified_records > 0:
            print("✅ Success! Stage 1 data is now properly linked to metadata")
            return True
        else:
            print("❌ No records have interview_id mapping after update")
            return False
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing Stage 1 data with interview ID as primary key...")
    success = fix_stage1_with_metadata()
    
    if success:
        print("\n🎉 Stage 1 data successfully updated with proper interview ID mapping!")
    else:
        print("\n❌ Failed to update Stage 1 data")
        sys.exit(1) 