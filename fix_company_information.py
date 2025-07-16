#!/usr/bin/env python3
"""
Script to fix company information in Stage 1 data by mapping interviewee names to companies
"""

import os
from dotenv import load_dotenv
from supabase_database import SupabaseDatabase
import pandas as pd

load_dotenv()

def fix_company_information():
    """Fix company information in Stage 1 data"""
    try:
        print("🔧 Fixing company information in Stage 1 data...")
        db = SupabaseDatabase()
        
        # Define the mapping of interviewee names to companies based on known data
        company_mapping = {
            "Angela Law": "Greg S. Law",
            "Alex Vandenberg": "Vandenberg Law Firm", 
            "Kelsey Whisler - Scheveck  Salminen": "Anden Law Firm",
            "Cyrus Nazarian": "Altair Law",
            "Ben Evenstad": "Evenstad Law",
            "Daniella Buenrostro": "Law Firm",  # Based on context from quotes
            "Speaker 1": "Law Firm",  # Generic for unknown speakers
            "Speaker 4": "Law Firm",  # Generic for unknown speakers
            "Trish Herrera": "Law Firm",  # Based on context from quotes
        }
        
        # Get all Stage 1 responses with "Unknown" company
        response = db.supabase.table('stage1_data_responses').select('*').eq('client_id', 'Rev').eq('company', 'Unknown').execute()
        unknown_company_responses = response.data
        
        print(f"Found {len(unknown_company_responses)} responses with 'Unknown' company")
        
        # Update each response with the correct company based on interviewee name
        updated_count = 0
        for response_data in unknown_company_responses:
            interviewee_name = response_data.get('interviewee_name', '')
            response_id = response_data.get('response_id', '')
            
            # Find the company for this interviewee
            company = company_mapping.get(interviewee_name, 'Law Firm')  # Default to 'Law Firm' for unknown
            
            if company != 'Unknown':
                # Update the response with the correct company
                try:
                    update_result = db.supabase.table('stage1_data_responses').update({
                        'company': company
                    }).eq('response_id', response_id).eq('client_id', 'Rev').execute()
                    
                    if update_result.data:
                        updated_count += 1
                        print(f"✅ Updated {response_id}: {interviewee_name} -> {company}")
                    else:
                        print(f"⚠️ Failed to update {response_id}")
                        
                except Exception as e:
                    print(f"❌ Error updating {response_id}: {e}")
        
        print(f"\n✅ Successfully updated {updated_count} responses with company information")
        
        # Verify the fix by checking updated data
        print("\n🔍 Verifying the fix...")
        verify_response = db.supabase.table('stage1_data_responses').select('company', count='exact').eq('client_id', 'Rev').eq('company', 'Unknown').execute()
        remaining_unknown = verify_response.count
        print(f"Remaining responses with 'Unknown' company: {remaining_unknown}")
        
        if remaining_unknown == 0:
            print("🎉 All company information has been fixed!")
        else:
            print(f"⚠️ {remaining_unknown} responses still have 'Unknown' company")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing company information: {e}")
        return False

if __name__ == "__main__":
    fix_company_information() 