#!/usr/bin/env python3

import pandas as pd
import sqlite3
import os
from datetime import datetime
import argparse

def migrate_csv_to_database(csv_path: str, db_path: str = "voc_pipeline.db"):
    """
    Migrate Stage 1 CSV data to the new database schema
    """
    print(f"🔄 Migrating {csv_path} to database {db_path}")
    
    # Read CSV file
    try:
        df = pd.read_csv(csv_path)
        print(f"📊 Loaded {len(df)} quotes from CSV")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return False
    
    # Connect to database
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Ensure table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS core_responses (
                response_id VARCHAR PRIMARY KEY,
                verbatim_response TEXT,
                subject VARCHAR,
                question TEXT,
                deal_status VARCHAR,
                company VARCHAR,
                interviewee_name VARCHAR,
                interview_date DATE,
                file_source VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert data
        migrated_count = 0
        for _, row in df.iterrows():
            try:
                # Parse date if it exists
                interview_date = None
                if 'date_of_interview' in row and pd.notna(row['date_of_interview']):
                    try:
                        # Try different date formats
                        date_str = str(row['date_of_interview'])
                        if '/' in date_str:
                            interview_date = datetime.strptime(date_str, '%m/%d/%Y').date()
                        elif '-' in date_str:
                            interview_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except:
                        interview_date = None
                
                cursor.execute("""
                    INSERT OR REPLACE INTO core_responses 
                    (response_id, verbatim_response, subject, question, deal_status, 
                     company, interviewee_name, interview_date, file_source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('response_id', ''),
                    row.get('verbatim_response', ''),
                    row.get('subject', ''),
                    row.get('question', ''),
                    row.get('deal_status', ''),
                    row.get('company', ''),
                    row.get('interviewee_name', ''),
                    interview_date,
                    csv_path  # Use CSV filename as source
                ))
                migrated_count += 1
                
            except Exception as e:
                print(f"⚠️ Error migrating row {row.get('response_id', 'unknown')}: {e}")
                continue
        
        conn.commit()
        print(f"✅ Successfully migrated {migrated_count} quotes to database")
        
        # Show summary
        cursor.execute("SELECT COUNT(*) FROM core_responses")
        total_in_db = cursor.fetchone()[0]
        print(f"📊 Total quotes in database: {total_in_db}")
        
        # Show companies
        cursor.execute("SELECT company, COUNT(*) FROM core_responses GROUP BY company")
        companies = cursor.fetchall()
        print(f"🏢 Companies in database:")
        for company, count in companies:
            print(f"  {company}: {count} quotes")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Migrate Stage 1 CSV to database')
    parser.add_argument('csv_path', help='Path to Stage 1 CSV file')
    parser.add_argument('--db', default='voc_pipeline.db', help='Database path (default: voc_pipeline.db)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_path):
        print(f"❌ CSV file not found: {args.csv_path}")
        return
    
    success = migrate_csv_to_database(args.csv_path, args.db)
    if success:
        print(f"\n🎉 Migration complete! You can now run Stage 2 analysis with:")
        print(f"python enhanced_stage2_analyzer.py")
    else:
        print(f"\n❌ Migration failed")

if __name__ == "__main__":
    main() 