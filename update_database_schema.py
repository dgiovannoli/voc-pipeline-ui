#!/usr/bin/env python3
"""
Update existing database schema to add sync_status columns for Supabase integration
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_database_schema():
    """Update existing database to add sync_status columns"""
    
    with sqlite3.connect("voc_pipeline.db") as conn:
        cursor = conn.cursor()
        
        # Check if sync_status column exists in core_responses
        cursor.execute("PRAGMA table_info(core_responses)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'sync_status' not in columns:
            logger.info("Adding sync_status column to core_responses table...")
            cursor.execute("ALTER TABLE core_responses ADD COLUMN sync_status VARCHAR DEFAULT 'local_only'")
            logger.info("✅ Added sync_status to core_responses")
        else:
            logger.info("sync_status column already exists in core_responses")
        
        # Check if sync_status column exists in quote_analysis
        cursor.execute("PRAGMA table_info(quote_analysis)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'sync_status' not in columns:
            logger.info("Adding sync_status column to quote_analysis table...")
            cursor.execute("ALTER TABLE quote_analysis ADD COLUMN sync_status VARCHAR DEFAULT 'local_only'")
            logger.info("✅ Added sync_status to quote_analysis")
        else:
            logger.info("sync_status column already exists in quote_analysis")
        
        # Create sync_tracking table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_tracking (
                sync_id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name VARCHAR NOT NULL,
                record_id VARCHAR NOT NULL,
                sync_direction VARCHAR CHECK (sync_direction IN ('to_cloud', 'from_cloud')),
                sync_status VARCHAR CHECK (sync_status IN ('pending', 'success', 'failed')),
                sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                error_message TEXT
            )
        """)
        logger.info("✅ Created sync_tracking table")
        
        # Update existing records to have sync_status
        cursor.execute("UPDATE core_responses SET sync_status = 'local_only' WHERE sync_status IS NULL")
        cursor.execute("UPDATE quote_analysis SET sync_status = 'local_only' WHERE sync_status IS NULL")
        
        conn.commit()
        
        # Show updated schema
        logger.info("\n📊 Updated Database Schema:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            logger.info(f"\n{table_name}:")
            for col in columns:
                logger.info(f"  - {col[1]} ({col[2]})")
        
        # Show record counts
        cursor.execute("SELECT COUNT(*) FROM core_responses")
        response_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM quote_analysis")
        analysis_count = cursor.fetchone()[0]
        
        logger.info(f"\n📈 Record Counts:")
        logger.info(f"  - core_responses: {response_count}")
        logger.info(f"  - quote_analysis: {analysis_count}")

if __name__ == "__main__":
    update_database_schema() 