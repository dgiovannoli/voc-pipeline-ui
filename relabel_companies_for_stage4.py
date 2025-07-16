#!/usr/bin/env python3
"""
Script to relabel companies in Stage 1 data with proper company identifiers
for accurate Stage 4 cross-company validation testing
"""

import os
from dotenv import load_dotenv
from supabase_database import SupabaseDatabase
import pandas as pd

load_dotenv()

def relabel_companies_for_stage4():
    """Relabel companies with proper identifiers for Stage 4 testing"""
    try:
        print("🔧 Relabeling companies for Stage 4 testing...")
        db = SupabaseDatabase()
        
        # Get all unique companies from Stage 1 data
        response = db.supabase.table('stage1_data_responses').select('company').eq('client_id', 'Rev').execute()
        stage1_data = response.data
        
        if not stage1_data:
            print("❌ No Stage 1 data found")
            return False
            
        df = pd.DataFrame(stage1_data)
        unique_companies = df['company'].unique()
        
        print(f"📊 Found {len(unique_companies)} unique companies:")
        for company in unique_companies:
            print(f"  - {company}")
        
        # Create mapping of companies to identifiers
        # Sort companies to ensure consistent mapping
        sorted_companies = sorted(unique_companies)
        company_mapping = {}
        
        # Assign Company A-Z identifiers
        for i, company in enumerate(sorted_companies):
            if i < 26:  # A-Z
                identifier = f"Company {chr(65 + i)}"  # 65 is ASCII for 'A'
                company_mapping[company] = identifier
                print(f"  {company} → {identifier}")
            else:
                # If more than 26 companies, use Company AA, BB, etc.
                identifier = f"Company {chr(65 + (i // 26) - 1)}{chr(65 + (i % 26))}"
                company_mapping[company] = identifier
                print(f"  {company} → {identifier}")
        
        # Update Stage 1 data with new company identifiers
        print("\n🔄 Updating Stage 1 data...")
        updated_count = 0
        
        for old_company, new_company in company_mapping.items():
            if old_company != new_company:  # Only update if different
                response = db.supabase.table('stage1_data_responses').update({
                    'company': new_company
                }).eq('client_id', 'Rev').eq('company', old_company).execute()
                
                if response.data:
                    updated_count += len(response.data)
                    print(f"  ✅ Updated {len(response.data)} records: {old_company} → {new_company}")
        
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
        
        return True
        
    except Exception as e:
        print(f"❌ Error relabeling companies: {e}")
        return False

def create_metadata_upload_process():
    """Create a metadata upload process for future use"""
    print("\n📝 Creating metadata upload process...")
    
    metadata_template = """# Metadata Upload Process

## Current Company Mapping
The following companies have been assigned identifiers for Stage 4 testing:

"""
    
    # Get the current mapping
    try:
        db = SupabaseDatabase()
        response = db.supabase.table('stage1_data_responses').select('company').eq('client_id', 'Rev').execute()
        stage1_data = response.data
        
        if stage1_data:
            df = pd.DataFrame(stage1_data)
            unique_companies = sorted(df['company'].unique())
            
            for company in unique_companies:
                metadata_template += f"- {company}\n"
            
            metadata_template += """

## Future Metadata Upload Process

To upload metadata for new interviews:

1. **Prepare Metadata CSV** with columns:
   - interviewee_name
   - company_name
   - interview_date
   - deal_status
   - other_relevant_fields

2. **Upload Process**:
   ```python
   from metadata_uploader import MetadataUploader
   
   uploader = MetadataUploader()
   uploader.upload_metadata('path/to/metadata.csv', client_id='Rev')
   ```

3. **Validation**:
   - Ensure all required fields are present
   - Validate company names against existing mapping
   - Check for duplicate interviewee names

## Notes
- Company identifiers are automatically assigned (Company A, Company B, etc.)
- Cross-company validation requires minimum 2 companies per theme
- Strategic alerts can be single-company for urgent issues
"""
        
        # Save the metadata template
        with open('metadata_upload_guide.md', 'w') as f:
            f.write(metadata_template)
        
        print("✅ Created metadata upload guide: metadata_upload_guide.md")
        
    except Exception as e:
        print(f"❌ Error creating metadata upload process: {e}")

if __name__ == "__main__":
    print("🚀 Starting company relabeling process...")
    
    # Relabel companies
    success = relabel_companies_for_stage4()
    
    if success:
        # Create metadata upload process
        create_metadata_upload_process()
        
        print("\n🎉 Company relabeling complete!")
        print("📋 Next steps:")
        print("  1. Run Stage 3 analysis to regenerate findings with proper company data")
        print("  2. Run Stage 4 analysis to test cross-company validation")
        print("  3. Review the metadata_upload_guide.md for future metadata uploads")
    else:
        print("\n❌ Company relabeling failed!") 