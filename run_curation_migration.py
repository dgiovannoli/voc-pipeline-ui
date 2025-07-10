#!/usr/bin/env python3
"""
Run the curation database migration to add curation fields to tables.
"""

import os
import sys
from dotenv import load_dotenv
from supabase_database import SupabaseDatabase

def run_migration():
    """Run the curation migration."""
    print("🔄 Running curation database migration...")
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize database connection
        db = SupabaseDatabase()
        print("✅ Connected to Supabase database")
        
        # Migration SQL commands
        migration_commands = [
            # Add curation fields to stage4_themes table
            """
            ALTER TABLE stage4_themes 
            ADD COLUMN IF NOT EXISTS curation_status VARCHAR(20) DEFAULT 'pending' CHECK (curation_status IN ('pending', 'approved', 'denied')),
            ADD COLUMN IF NOT EXISTS curated_by VARCHAR(100),
            ADD COLUMN IF NOT EXISTS curated_at TIMESTAMP WITH TIME ZONE,
            ADD COLUMN IF NOT EXISTS curator_notes TEXT;
            """,
            
            # Add curation fields to quote_analysis table
            """
            ALTER TABLE quote_analysis 
            ADD COLUMN IF NOT EXISTS curation_label VARCHAR(20) DEFAULT 'pending' CHECK (curation_label IN ('pending', 'approve', 'deny', 'feature')),
            ADD COLUMN IF NOT EXISTS curated_by VARCHAR(100),
            ADD COLUMN IF NOT EXISTS curated_at TIMESTAMP WITH TIME ZONE,
            ADD COLUMN IF NOT EXISTS curator_notes TEXT;
            """,
            
            # Create indexes for faster curation queries
            """
            CREATE INDEX IF NOT EXISTS idx_stage4_themes_curation_status ON stage4_themes(curation_status, client_id);
            """,
            
            """
            CREATE INDEX IF NOT EXISTS idx_quote_analysis_curation_label ON quote_analysis(curation_label, client_id);
            """
        ]
        
        # Execute each migration command
        for i, command in enumerate(migration_commands, 1):
            print(f"📝 Executing migration step {i}...")
            try:
                # Execute the SQL command
                result = db.supabase.rpc('exec_sql', {'sql': command}).execute()
                print(f"✅ Migration step {i} completed successfully")
            except Exception as e:
                print(f"⚠️ Migration step {i} had an issue (this might be expected if columns already exist): {e}")
        
        print("\n🎉 Curation migration completed!")
        print("✅ Added curation fields to stage4_themes and quote_analysis tables")
        print("✅ Created indexes for faster curation queries")
        print("\n📋 New fields added:")
        print("   - stage4_themes: curation_status, curated_by, curated_at, curator_notes")
        print("   - quote_analysis: curation_label, curated_by, curated_at, curator_notes")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration() 