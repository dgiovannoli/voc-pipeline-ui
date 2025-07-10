"""
Check the current state of the interview_id column in stage2_response_labeling table
"""

import pandas as pd
from supabase_database import SupabaseDatabase

def check_interview_id_column():
    """Check the current state of interview_id column"""
    
    db = SupabaseDatabase()
    
    try:
        # Get a sample of stage2_response_labeling data to check columns
        quotes_df = db.get_scored_quotes('Rev')
        
        print("📊 Current stage2_response_labeling columns:")
        print(f"Columns: {list(quotes_df.columns)}")
        
        # Check if interview_id exists
        if 'interview_id' in quotes_df.columns:
            print("✅ interview_id column exists!")
            
            # Check data types and null values
            print(f"\n📋 interview_id column info:")
            print(f"Data type: {quotes_df['interview_id'].dtype}")
            print(f"Null values: {quotes_df['interview_id'].isnull().sum()}")
            print(f"Total rows: {len(quotes_df)}")
            
            # Show sample values
            print(f"\n📝 Sample interview_id values:")
            sample_values = quotes_df['interview_id'].dropna().head(10)
            if not sample_values.empty:
                print(sample_values.value_counts().head())
            else:
                print("All values are NULL (not populated yet)")
                
        else:
            print("❌ interview_id column does not exist")
            
        # Show sample of other relevant columns
        print(f"\n🔍 Sample of response_id values (for mapping reference):")
        if 'response_id' in quotes_df.columns:
            print(quotes_df['response_id'].head(5).tolist())
            
    except Exception as e:
        print(f"❌ Error checking column: {e}")

if __name__ == "__main__":
    print("🔍 Checking interview_id column status...")
    check_interview_id_column() 