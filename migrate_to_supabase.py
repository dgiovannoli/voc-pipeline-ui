#!/usr/bin/env python3
"""
Migration script to move from SQLite to Supabase-only architecture
This script helps migrate existing data and clean up SQLite dependencies
"""

import os
import sqlite3
import pandas as pd
from datetime import datetime
import logging
from dotenv import load_dotenv

# Import Supabase database manager
from supabase_database import SupabaseDatabase

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_sqlite_data():
    """Check what data exists in SQLite database"""
    if not os.path.exists("voc_pipeline.db"):
        logger.info("No SQLite database found")
        return None
    
    try:
        with sqlite3.connect("voc_pipeline.db") as conn:
            cursor = conn.cursor()
            
            # Check core_responses
            cursor.execute("SELECT COUNT(*) FROM core_responses")
            core_count = cursor.fetchone()[0]
            
            # Check quote_analysis
            cursor.execute("SELECT COUNT(*) FROM quote_analysis")
            analysis_count = cursor.fetchone()[0]
            
            logger.info(f"SQLite database contains:")
            logger.info(f"  - {core_count} core responses")
            logger.info(f"  - {analysis_count} quote analyses")
            
            return {
                'core_responses': core_count,
                'quote_analysis': analysis_count
            }
    except Exception as e:
        logger.error(f"Error checking SQLite data: {e}")
        return None

def migrate_sqlite_to_supabase():
    """Migrate data from SQLite to Supabase"""
    if not os.path.exists("voc_pipeline.db"):
        logger.warning("No SQLite database found to migrate")
        return False
    
    try:
        # Initialize Supabase
        db = SupabaseDatabase()
        logger.info("✅ Supabase connection established")
        
        # Migrate core_responses
        with sqlite3.connect("voc_pipeline.db") as conn:
            core_df = pd.read_sql_query("SELECT * FROM core_responses", conn)
            
            if not core_df.empty:
                logger.info(f"Migrating {len(core_df)} core responses...")
                migrated_count = 0
                
                for _, row in core_df.iterrows():
                    response_data = {
                        'response_id': row.get('response_id', ''),
                        'verbatim_response': row.get('verbatim_response', ''),
                        'subject': row.get('subject', ''),
                        'question': row.get('question', ''),
                        'deal_status': row.get('deal_status', 'closed_won'),
                        'company': row.get('company', ''),
                        'interviewee_name': row.get('interviewee_name', ''),
                        'interview_date': row.get('interview_date', '2024-01-01'),
                        'file_source': row.get('file_source', 'sqlite_migration')
                    }
                    
                    if db.save_core_response(response_data):
                        migrated_count += 1
                
                logger.info(f"✅ Migrated {migrated_count} core responses")
            else:
                logger.info("No core responses to migrate")
            
            # Migrate quote_analysis
            analysis_df = pd.read_sql_query("SELECT * FROM quote_analysis", conn)
            
            if not analysis_df.empty:
                logger.info(f"Migrating {len(analysis_df)} quote analyses...")
                migrated_count = 0
                
                for _, row in analysis_df.iterrows():
                    analysis_data = {
                        'quote_id': row.get('quote_id', ''),
                        'criterion': row.get('criterion', ''),
                        'score': row.get('score', 0),
                        'priority': row.get('priority', 'medium'),
                        'confidence': row.get('confidence', 'medium'),
                        'relevance_explanation': row.get('relevance_explanation', ''),
                        'deal_weighted_score': row.get('deal_weighted_score', 0),
                        'context_keywords': row.get('context_keywords', ''),
                        'question_relevance': row.get('question_relevance', 'unrelated')
                    }
                    
                    if db.save_quote_analysis(analysis_data):
                        migrated_count += 1
                
                logger.info(f"✅ Migrated {migrated_count} quote analyses")
            else:
                logger.info("No quote analyses to migrate")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

def cleanup_sqlite_files():
    """Remove SQLite-related files after successful migration"""
    files_to_remove = [
        "voc_pipeline.db",
        "voc_pipeline.db.backup",
        "database.py",
        "supabase_integration.py",
        "update_database_schema.py",
        "db_explorer.py",
        "production_fix.py"
    ]
    
    removed_count = 0
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"🗑️ Removed {file_path}")
                removed_count += 1
            except Exception as e:
                logger.warning(f"⚠️ Could not remove {file_path}: {e}")
    
    logger.info(f"✅ Cleaned up {removed_count} SQLite-related files")
    return removed_count

def verify_migration():
    """Verify that migration was successful"""
    try:
        db = SupabaseDatabase()
        
        # Get summary statistics
        summary = db.get_summary_statistics()
        
        if "error" in summary:
            logger.error(f"❌ Migration verification failed: {summary['error']}")
            return False
        
        logger.info("✅ Migration verification successful:")
        logger.info(f"  - Total quotes: {summary['total_quotes']}")
        logger.info(f"  - Quotes analyzed: {summary['quotes_with_scores']}")
        logger.info(f"  - Coverage: {summary['coverage_percentage']}%")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration verification failed: {e}")
        return False

def main():
    """Main migration process"""
    logger.info("🚀 Starting SQLite to Supabase migration")
    logger.info("=" * 50)
    
    # Step 1: Check existing data
    logger.info("📊 Step 1: Checking existing SQLite data...")
    sqlite_data = check_sqlite_data()
    
    if not sqlite_data:
        logger.info("No SQLite data found. Migration not needed.")
        return
    
    # Step 2: Migrate data
    logger.info("🔄 Step 2: Migrating data to Supabase...")
    if not migrate_sqlite_to_supabase():
        logger.error("❌ Migration failed. Stopping.")
        return
    
    # Step 3: Verify migration
    logger.info("✅ Step 3: Verifying migration...")
    if not verify_migration():
        logger.error("❌ Migration verification failed. Data may be incomplete.")
        return
    
    # Step 4: Cleanup (optional)
    logger.info("🗑️ Step 4: Cleaning up SQLite files...")
    cleanup_sqlite_files()
    
    logger.info("🎉 Migration completed successfully!")
    logger.info("=" * 50)
    logger.info("Your VOC Pipeline is now using Supabase exclusively.")
    logger.info("You can now run the application with: streamlit run app.py")

if __name__ == "__main__":
    main() 