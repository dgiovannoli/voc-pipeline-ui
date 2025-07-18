#!/usr/bin/env python3

import os
import re
from supabase_database import SupabaseDatabase

def test_interview_id_extraction():
    """Test interview ID extraction from transcript files"""
    
    print("🔍 Testing interview ID extraction...")
    
    # Test with a sample file
    test_file = "Context/Interview with Alex Vandenberg.txt"
    
    if os.path.exists(test_file):
        print(f"📁 Testing with file: {test_file}")
        
        # Extract interview ID
        interview_id = extract_interview_id_from_file(test_file)
        
        if interview_id:
            print(f"✅ Successfully extracted interview ID: {interview_id}")
            
            # Test metadata lookup
            db = SupabaseDatabase()
            metadata = get_metadata_for_interview_id(interview_id, "Rev")
            
            if metadata:
                print(f"✅ Found metadata for {interview_id}:")
                print(f"  - Interviewee: {metadata.get('interviewee_name', 'N/A')}")
                print(f"  - Company: {metadata.get('company', 'N/A')}")
                print(f"  - Deal Status: {metadata.get('deal_status', 'N/A')}")
                print(f"  - Date: {metadata.get('date_of_interview', 'N/A')}")
            else:
                print(f"❌ No metadata found for {interview_id}")
        else:
            print(f"❌ No interview ID found in {test_file}")
    else:
        print(f"❌ Test file not found: {test_file}")

def extract_interview_id_from_file(file_path: str) -> str:
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
                
                # Pattern: Interview ID: XXXXX
                match = re.search(r'Interview ID:\s*([A-Z0-9-]+)', line, re.IGNORECASE)
                if match:
                    return match.group(1)
                
                # Pattern: ID: XXXXX
                match = re.search(r'ID:\s*([A-Z0-9-]+)', line, re.IGNORECASE)
                if match:
                    return match.group(1)
        
        return ""
    except Exception as e:
        print(f"Could not extract interview ID from {file_path}: {e}")
        return ""

def get_metadata_for_interview_id(interview_id: str, client_id: str):
    """Get metadata for a given interview ID from the database"""
    if not interview_id:
        return {}
    
    try:
        db = SupabaseDatabase()
        # Query the metadata table for this interview ID
        response = db.supabase.table('interview_metadata').select('*').eq('interview_id', interview_id).eq('client_id', client_id).execute()
        
        if response.data:
            metadata = response.data[0]
            return {
                'interviewee_name': metadata.get('interviewee_name', ''),
                'company': metadata.get('company', ''),
                'deal_status': metadata.get('deal_status', ''),
                'date_of_interview': metadata.get('date_of_interview', ''),
                'interview_id': metadata.get('interview_id', '')
            }
        else:
            print(f"No metadata found for interview ID: {interview_id}")
            return {}
    except Exception as e:
        print(f"Error getting metadata for interview ID {interview_id}: {e}")
        return {}

if __name__ == "__main__":
    test_interview_id_extraction() 