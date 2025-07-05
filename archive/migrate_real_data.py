#!/usr/bin/env python3

import pandas as pd
import sqlite3
from enhanced_stage2_analyzer import DatabaseStage2Analyzer

def migrate_real_data():
    """Migrate the actual Stage 1 output data to the database"""
    
    print("🔄 Migrating real Stage 1 data to database...")
    
    # Initialize the analyzer (this creates the database schema)
    analyzer = DatabaseStage2Analyzer()
    
    # Read the actual Stage 1 output
    df = pd.read_csv('stage1_output.csv')
    print(f"📊 Loaded {len(df)} responses from stage1_output.csv")
    
    # Fix column names to match database schema
    df = df.rename(columns={
        'date_of_interview': 'interview_date',
        'company': 'company'  # Keep as is
    })
    
    # Migrate to database
    with sqlite3.connect(analyzer.db_path) as conn:
        # Clear any existing data
        conn.execute("DELETE FROM core_responses")
        conn.execute("DELETE FROM quote_analysis")
        conn.execute("DELETE FROM trend_analysis")
        
        # Insert the real data
        df.to_sql('core_responses', conn, if_exists='append', index=False)
        
        # Verify the migration
        count = conn.execute("SELECT COUNT(*) FROM core_responses").fetchone()[0]
        print(f"✅ Successfully migrated {count} responses to database")
        
        # Show sample data
        sample = conn.execute("SELECT response_id, verbatim_response FROM core_responses LIMIT 3").fetchall()
        print("\n📋 Sample responses:")
        for response_id, verbatim in sample:
            print(f"  {response_id}: {verbatim[:100]}...")

if __name__ == "__main__":
    migrate_real_data() 