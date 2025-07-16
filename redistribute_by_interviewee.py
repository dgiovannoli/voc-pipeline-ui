#!/usr/bin/env python3
"""
Script to redistribute companies based on unique interviewee names
for accurate Stage 4 cross-company validation testing
"""

import os
from dotenv import load_dotenv
from supabase_database import SupabaseDatabase
import pandas as pd

load_dotenv()

def redistribute_companies_by_interviewee():
    """Redistribute companies based on unique interviewee names"""
    try:
        print("🔧 Redistributing companies based on interviewee names...")
        db = SupabaseDatabase()
        
        # Get all Stage 1 data
        response = db.supabase.table('stage1_data_responses').select('*').eq('client_id', 'Rev').execute()
        stage1_data = response.data
        
        if not stage1_data:
            print("❌ No Stage 1 data found")
            return False
            
        df = pd.DataFrame(stage1_data)
        
        # Get unique interviewees (excluding generic names like "Speaker 1", "Unknown")
        unique_interviewees = df['interviewee_name'].unique()
        
        # Filter out generic speaker names and create proper company mapping
        valid_interviewees = []
        for name in unique_interviewees:
            if name and name not in ['Speaker 1', 'Speaker 3', 'Speaker 4', 'Speakers', 'Unknown']:
                valid_interviewees.append(name)
        
        print(f"📊 Found {len(valid_interviewees)} valid interviewees:")
        for name in valid_interviewees:
            count = len(df[df['interviewee_name'] == name])
            print(f"  - {name}: {count} responses")
        
        # Create company mapping based on interviewee names
        company_mapping = {}
        for i, interviewee in enumerate(sorted(valid_interviewees)):
            if i < 26:  # A-Z
                company_id = f"Company {chr(65 + i)}"
                company_mapping[interviewee] = company_id
                print(f"  {interviewee} → {company_id}")
            else:
                # If more than 26, use Company AA, BB, etc.
                company_id = f"Company {chr(65 + (i // 26) - 1)}{chr(65 + (i % 26))}"
                company_mapping[interviewee] = company_id
                print(f"  {interviewee} → {company_id}")
        
        # Handle generic speakers by assigning them to existing companies
        # This ensures we don't lose data while maintaining cross-company validation
        speaker_mapping = {
            'Speaker 1': 'Company A',  # Assign to first company
            'Speaker 3': 'Company B',  # Assign to second company  
            'Speaker 4': 'Company C',  # Assign to third company
            'Speakers': 'Company D',   # Assign to fourth company
            'Unknown': 'Company E'     # Assign to fifth company
        }
        
        # Update Stage 1 data with new company assignments
        print("\n🔄 Updating Stage 1 data...")
        updated_count = 0
        
        # Update based on interviewee names
        for interviewee, company_id in company_mapping.items():
            response = db.supabase.table('stage1_data_responses').update({
                'company': company_id
            }).eq('client_id', 'Rev').eq('interviewee_name', interviewee).execute()
            
            if response.data:
                updated_count += len(response.data)
                print(f"  ✅ Updated {len(response.data)} records: {interviewee} → {company_id}")
        
        # Update generic speakers
        for speaker, company_id in speaker_mapping.items():
            response = db.supabase.table('stage1_data_responses').update({
                'company': company_id
            }).eq('client_id', 'Rev').eq('interviewee_name', speaker).execute()
            
            if response.data:
                updated_count += len(response.data)
                print(f"  ✅ Updated {len(response.data)} records: {speaker} → {company_id}")
        
        print(f"\n✅ Successfully updated {updated_count} records")
        
        # Verify the changes
        print("\n📋 Verification - New company distribution:")
        response = db.supabase.table('stage1_data_responses').select('company').eq('client_id', 'Rev').execute()
        stage1_data = response.data
        
        if stage1_data:
            df = pd.DataFrame(stage1_data)
            company_counts = df['company'].value_counts()
            print(f"Total responses: {len(df)}")
            for company, count in company_counts.items():
                print(f"  {company}: {count}")
        
        # Show interviewee distribution per company
        print("\n👥 Interviewee distribution per company:")
        response = db.supabase.table('stage1_data_responses').select('interviewee_name,company').eq('client_id', 'Rev').execute()
        stage1_data = response.data
        
        if stage1_data:
            df = pd.DataFrame(stage1_data)
            for company in sorted(df['company'].unique()):
                interviewees = df[df['company'] == company]['interviewee_name'].unique()
                count = len(df[df['company'] == company])
                print(f"  {company}: {count} responses from {len(interviewees)} interviewee(s)")
                for interviewee in interviewees:
                    interviewee_count = len(df[(df['company'] == company) & (df['interviewee_name'] == interviewee)])
                    print(f"    - {interviewee}: {interviewee_count} responses")
        
        return True
        
    except Exception as e:
        print(f"❌ Error redistributing companies: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting company redistribution process...")
    
    success = redistribute_companies_by_interviewee()
    
    if success:
        print("\n🎉 Company redistribution complete!")
        print("📋 Next steps:")
        print("  1. Run Stage 3 analysis to regenerate findings with proper company data")
        print("  2. Run Stage 4 analysis to test cross-company validation")
        print("  3. The distribution should now be much more balanced for accurate testing")
    else:
        print("\n❌ Company redistribution failed!") 