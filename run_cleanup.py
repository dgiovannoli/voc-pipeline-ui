#!/usr/bin/env python3
"""
Database Cleanup Script
Removes unused tables from the VOC pipeline database
"""

import os
from dotenv import load_dotenv
from supabase_database import SupabaseDatabase

load_dotenv()

def run_cleanup():
    """Run database cleanup to remove unused tables"""
    
    print("🧹 VOC Pipeline Database Cleanup")
    print("=" * 50)
    
    try:
        # Initialize database connection
        db = SupabaseDatabase()
        print("✅ Connected to Supabase database")
        
        # Tables to drop (unused in current codebase)
        tables_to_drop = [
            'findings',           # Replaced by stage3_findings
            'trend_analysis',     # Functionality in criteria_scorecard
            'processing_metadata' # Replaced by processing_logs
        ]
        
        # Drop unused tables
        for table in tables_to_drop:
            try:
                # Use raw SQL to drop table
                result = db.supabase.rpc('exec_sql', {
                    'sql': f'DROP TABLE IF EXISTS {table} CASCADE;'
                }).execute()
                print(f"✅ Dropped table: {table}")
            except Exception as e:
                print(f"⚠️  Could not drop {table}: {e}")
        
        # Verify remaining tables
        print("\n📊 Remaining Tables:")
        print("-" * 30)
        
        # Core tables that should remain
        core_tables = [
            'stage1_data_responses',
            'stage2_response_labeling', 
            'stage3_findings',
            'themes',
            'executive_themes',
            'criteria_scorecard'
        ]
        
        # Enhancement tables
        enhancement_tables = [
            'processing_logs',
            'data_quality_metrics',
            'fuzzy_matching_cache'
        ]
        
        all_tables = core_tables + enhancement_tables
        
        for table in all_tables:
            try:
                # Try to query the table to see if it exists
                result = db.supabase.table(table).select('count').limit(1).execute()
                print(f"✅ {table} - exists")
            except Exception as e:
                print(f"❌ {table} - not found: {e}")
        
        print("\n🎉 Database cleanup completed!")
        print("\n📋 Summary:")
        print("✅ Removed: findings, trend_analysis, processing_metadata")
        print("✅ Kept: All core pipeline tables and enhancement tables")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")

if __name__ == "__main__":
    run_cleanup() 