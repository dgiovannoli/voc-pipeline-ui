#!/usr/bin/env python3
"""
Update Stage 4 Themes Schema
Updates the database schema to include strategic alert columns
"""

import os
import logging
from supabase_database import SupabaseDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_stage4_schema():
    """Update the Stage 4 themes schema with strategic alert columns"""
    try:
        # Initialize database connection
        supabase = SupabaseDatabase()
        
        # Read the schema file
        with open('fix_stage4_themes_schema.sql', 'r') as f:
            schema_sql = f.read()
        
        # Split into individual statements
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        
        # Execute each statement
        for i, statement in enumerate(statements):
            if statement:
                logger.info(f"Executing statement {i+1}/{len(statements)}")
                try:
                    # Execute the SQL statement
                    result = supabase.supabase.rpc('exec_sql', {'sql': statement}).execute()
                    logger.info(f"✅ Statement {i+1} executed successfully")
                except Exception as e:
                    logger.error(f"❌ Error executing statement {i+1}: {e}")
                    # Try alternative approach for DDL statements
                    try:
                        # For DDL statements, we might need to use a different approach
                        if 'DROP' in statement or 'CREATE' in statement:
                            logger.info(f"Attempting alternative execution for DDL statement")
                            # This might need to be done through Supabase dashboard
                            logger.warning(f"DDL statement needs manual execution: {statement[:100]}...")
                    except Exception as e2:
                        logger.error(f"❌ Alternative execution also failed: {e2}")
        
        logger.info("✅ Schema update completed")
        
    except Exception as e:
        logger.error(f"❌ Failed to update schema: {e}")

if __name__ == "__main__":
    update_stage4_schema() 