#!/usr/bin/env python3
"""
Migration script to add new columns to stage2_response_labeling table
"""

import os
from supabase_database import SupabaseDatabase

def run_migration():
    """Run the migration to add new columns"""
    try:
        db = SupabaseDatabase()
        
        # Execute each ALTER TABLE statement separately
        print("Adding secondary_criterion column...")
        db.supabase.table('stage2_response_labeling').update({}).eq('id', 0).execute()  # Dummy query to test connection
        
        # Since we can't execute DDL directly, let's check if the columns exist first
        print("Checking current columns...")
        result = db.supabase.table('stage2_response_labeling').select('*').limit(1).execute()
        columns = list(result.data[0].keys()) if result.data else []
        print(f"Current columns: {columns}")
        
        # For now, let's just update the analyzer to work with existing columns
        # and we'll add the new columns manually in the database
        print("⚠️  Please run the following SQL manually in your Supabase dashboard:")
        print("""
ALTER TABLE stage2_response_labeling 
ADD COLUMN IF NOT EXISTS secondary_criterion VARCHAR(100),
ADD COLUMN IF NOT EXISTS tertiary_criterion VARCHAR(100),
ADD COLUMN IF NOT EXISTS all_relevance_scores JSONB;
        """)
                
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    run_migration() 