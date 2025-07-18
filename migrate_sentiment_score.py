#!/usr/bin/env python3
"""
Migration script to add sentiment_score column to stage2_response_labeling table
"""

import os
from supabase_database import SupabaseDatabase

def run_migration():
    """Run the migration to add sentiment_score column"""
    try:
        db = SupabaseDatabase()
        
        # Read the SQL file
        with open('add_sentiment_score_column.sql', 'r') as f:
            sql = f.read()
        
        # Split into individual statements
        statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
        
        print("Running sentiment score migration...")
        
        # Execute each statement separately
        for i, statement in enumerate(statements, 1):
            if statement:
                print(f"Executing statement {i}/{len(statements)}...")
                try:
                    # For ALTER TABLE and CREATE INDEX, we need to use raw SQL
                    # Since Supabase doesn't support DDL through the REST API directly,
                    # we'll check if the column exists first
                    if 'ADD COLUMN' in statement:
                        # Check if column already exists
                        result = db.supabase.table('stage2_response_labeling').select('*').limit(1).execute()
                        if result.data:
                            # Try to access sentiment_score to see if it exists
                            try:
                                test_result = db.supabase.table('stage2_response_labeling').select('sentiment_score').limit(1).execute()
                                print("✅ sentiment_score column already exists")
                            except:
                                print("⚠️  sentiment_score column does not exist - manual migration may be needed")
                                print("Please run the SQL manually in your Supabase dashboard:")
                                print(statement)
                    elif 'CREATE INDEX' in statement:
                        print("⚠️  Index creation may need manual execution in Supabase dashboard")
                        print(statement)
                    elif 'UPDATE' in statement:
                        print("⚠️  Data update may need manual execution in Supabase dashboard")
                        print(statement)
                    else:
                        print(f"Statement: {statement}")
                        
                except Exception as e:
                    print(f"⚠️  Statement {i} failed: {e}")
                    print(f"Statement: {statement}")
        
        print("✅ Migration script completed")
        
        # Verify the column was added
        print("Verifying new column...")
        try:
            result = db.supabase.table('stage2_response_labeling').select('sentiment_score').limit(1).execute()
            print("✅ sentiment_score column is accessible")
        except Exception as e:
            print(f"⚠️  sentiment_score column not accessible: {e}")
            print("You may need to run the migration manually in your Supabase dashboard")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_migration() 