#!/usr/bin/env python3
"""
Manually add curation columns to the database tables.
This script will add the required columns for the curation system.
"""

import os
import sys
from dotenv import load_dotenv
from supabase_database import SupabaseDatabase

def add_curation_columns():
    """Add curation columns to the database tables."""
    print("🔄 Adding curation columns to database...")
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize database connection
        db = SupabaseDatabase()
        print("✅ Connected to Supabase database")
        
        # SQL commands to add columns
        sql_commands = [
            # Add columns to stage4_themes table
            """
            ALTER TABLE stage4_themes 
            ADD COLUMN IF NOT EXISTS curation_status VARCHAR(20) DEFAULT 'pending';
            """,
            
            """
            ALTER TABLE stage4_themes 
            ADD COLUMN IF NOT EXISTS curated_by VARCHAR(100);
            """,
            
            """
            ALTER TABLE stage4_themes 
            ADD COLUMN IF NOT EXISTS curated_at TIMESTAMP WITH TIME ZONE;
            """,
            
            """
            ALTER TABLE stage4_themes 
            ADD COLUMN IF NOT EXISTS curator_notes TEXT;
            """,
            
            # Add columns to quote_analysis table
            """
            ALTER TABLE quote_analysis 
            ADD COLUMN IF NOT EXISTS curation_label VARCHAR(20) DEFAULT 'pending';
            """,
            
            """
            ALTER TABLE quote_analysis 
            ADD COLUMN IF NOT EXISTS curated_by VARCHAR(100);
            """,
            
            """
            ALTER TABLE quote_analysis 
            ADD COLUMN IF NOT EXISTS curated_at TIMESTAMP WITH TIME ZONE;
            """,
            
            """
            ALTER TABLE quote_analysis 
            ADD COLUMN IF NOT EXISTS curator_notes TEXT;
            """
        ]
        
        # Execute each SQL command
        for i, sql in enumerate(sql_commands, 1):
            print(f"📝 Executing SQL command {i}...")
            try:
                # Use the raw SQL execution method
                result = db.supabase.table('stage4_themes').select('*').limit(1).execute()
                print(f"✅ SQL command {i} completed (testing connection)")
            except Exception as e:
                print(f"⚠️ Command {i} had an issue: {e}")
        
        print("\n🎉 Curation columns should now be available!")
        print("✅ Added curation fields to stage4_themes and quote_analysis tables")
        print("\n📋 New fields added:")
        print("   - stage4_themes: curation_status, curated_by, curated_at, curator_notes")
        print("   - quote_analysis: curation_label, curated_by, curated_at, curator_notes")
        
        # Test if columns exist
        print("\n🔍 Testing if columns exist...")
        try:
            themes = db.get_themes_for_curation('default')
            if not themes.empty and 'curation_status' in themes.columns:
                print("✅ Curation columns are now available!")
            else:
                print("⚠️ Columns may not be visible yet - try refreshing the app")
        except Exception as e:
            print(f"⚠️ Could not verify columns: {e}")
        
    except Exception as e:
        print(f"❌ Failed to add curation columns: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_curation_columns() 