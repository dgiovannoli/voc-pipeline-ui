#!/usr/bin/env python3
"""
Add research question alignment columns to the database schema
"""

import sys
import os
from pathlib import Path
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from supabase_database import SupabaseDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_research_question_columns():
    """Add research question alignment columns to the database"""
    
    try:
        db = SupabaseDatabase()
        
        # SQL to add the new columns
        sql_commands = [
            """
            ALTER TABLE stage1_data_responses 
            ADD COLUMN IF NOT EXISTS research_question_alignment TEXT,
            ADD COLUMN IF NOT EXISTS total_questions_addressed INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS coverage_summary TEXT,
            ADD COLUMN IF NOT EXISTS stage2_analysis_timestamp TIMESTAMP WITH TIME ZONE
            """,
        ]
        
        for sql in sql_commands:
            logger.info(f"Executing SQL: {sql[:100]}...")
            result = db.supabase.rpc('exec_sql', {'sql': sql}).execute()
            logger.info(f"✅ SQL executed successfully")
        
        logger.info("✅ Research question alignment columns added successfully")
        
        # Verify the columns were added
        df = db.get_stage1_data_responses(client_id='Supio', limit=1)
        logger.info(f"Available columns after update: {df.columns.tolist()}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to add research question columns: {e}")
        return False

if __name__ == "__main__":
    success = add_research_question_columns()
    if success:
        print("✅ Research question columns added successfully")
    else:
        print("❌ Failed to add research question columns") 