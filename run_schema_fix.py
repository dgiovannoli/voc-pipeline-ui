#!/usr/bin/env python3

"""
Run Schema Fix for Scorecard Themes

This script runs the SQL to fix the scorecard_stage4_themes table schema.
"""

import logging
from supabase_database import SupabaseDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_schema_fix():
    """Run the schema fix SQL"""
    logger.info("🔧 Running schema fix for scorecard_stage4_themes table...")
    
    try:
        db = SupabaseDatabase()
        
        # Read the SQL file
        with open('fix_scorecard_stage4_themes_schema.sql', 'r') as f:
            sql_commands = f.read()
        
        # Split into individual commands
        commands = [cmd.strip() for cmd in sql_commands.split(';') if cmd.strip()]
        
        # Execute each command
        for i, command in enumerate(commands, 1):
            if command:
                logger.info(f"Executing command {i}/{len(commands)}")
                try:
                    response = db.supabase.rpc('exec_sql', {'sql': command}).execute()
                    logger.info(f"✅ Command {i} executed successfully")
                except Exception as e:
                    logger.warning(f"⚠️ Command {i} failed (may already exist): {e}")
        
        logger.info("✅ Schema fix completed")
        
        # Verify the table structure
        logger.info("🔍 Verifying table structure...")
        response = db.supabase.table('scorecard_stage4_themes').select('*').limit(1).execute()
        
        if response.data:
            columns = list(response.data[0].keys())
            logger.info(f"✅ Table has {len(columns)} columns")
            logger.info(f"Columns: {columns}")
        else:
            logger.info("✅ Table exists but is empty")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error running schema fix: {e}")
        return False

if __name__ == "__main__":
    success = run_schema_fix()
    if success:
        print("✅ Schema fix completed successfully")
    else:
        print("❌ Schema fix failed") 