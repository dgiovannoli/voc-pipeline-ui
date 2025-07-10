#!/usr/bin/env python3
"""
Database Cleanup Execution Script
Provides instructions and verification for database cleanup
"""

from supabase_database import SupabaseDatabase

def main():
    print("🗄️ Database Cleanup Execution")
    print("="*50)
    
    db = SupabaseDatabase()
    
    print("\n📋 Cleanup SQL Commands to Execute:")
    print("(Run these in your Supabase SQL editor or database client)")
    print("-" * 50)
    
    cleanup_commands = [
        "-- Remove unused columns from themes table",
        "ALTER TABLE themes DROP COLUMN IF EXISTS fuzzy_match_score;",
        "ALTER TABLE themes DROP COLUMN IF EXISTS semantic_group_id;",
        "ALTER TABLE themes DROP COLUMN IF EXISTS scorecard_theme_id;",
        "ALTER TABLE themes DROP COLUMN IF EXISTS synthesis_theme_id;",
        "",
        "-- Remove unused columns from stage3_findings table",
        "ALTER TABLE stage3_findings DROP COLUMN IF EXISTS scorecard_criterion_priority;",
        "ALTER TABLE stage3_findings DROP COLUMN IF EXISTS sentiment_alignment_score;"
    ]
    
    for cmd in cleanup_commands:
        print(cmd)
    
    print("\n🎯 How to Execute:")
    print("1. Go to your Supabase dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Copy and paste the commands above")
    print("4. Execute each command")
    print("5. Run this script again to verify cleanup")
    
    print("\n⚠️ Safety Notes:")
    print("- These columns are confirmed unused")
    print("- IF EXISTS clause prevents errors")
    print("- Backup your database first if concerned")
    
    # Verify current state
    print("\n🔍 Current Database State:")
    try:
        # Check themes table
        result = db.supabase.table('stage4_themes').select('*').limit(1).execute()
        if result.data:
            sample = result.data[0]
            print(f"  themes table columns: {list(sample.keys())}")
        
        # Check stage3_findings table
        result = db.supabase.table('stage3_findings').select('*').limit(1).execute()
        if result.data:
            sample = result.data[0]
            print(f"  stage3_findings table columns: {list(sample.keys())}")
            
    except Exception as e:
        print(f"  ❌ Error checking database: {e}")
    
    print("\n✅ Ready to proceed with cleanup!")

if __name__ == "__main__":
    main() 