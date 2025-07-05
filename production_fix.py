#!/usr/bin/env python3
"""
Production Database Fix Script
This script ensures the production environment uses the correct database with sync_status column.
"""

import os
import sqlite3
import shutil
from pathlib import Path
import sys

def get_database_path():
    """Get the absolute path to the database file"""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    db_path = script_dir / "voc_pipeline.db"
    return str(db_path)

def check_database_schema(db_path):
    """Check if the database has the correct schema"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if core_responses table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='core_responses'")
            if not cursor.fetchone():
                print(f"❌ Table 'core_responses' not found in {db_path}")
                return False
            
            # Check if sync_status column exists
            cursor.execute("PRAGMA table_info(core_responses)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'sync_status' not in columns:
                print(f"❌ Column 'sync_status' not found in core_responses table in {db_path}")
                return False
            
            print(f"✅ Database schema is correct in {db_path}")
            return True
            
    except Exception as e:
        print(f"❌ Error checking database schema: {e}")
        return False

def fix_database_schema(db_path):
    """Add sync_status column if it doesn't exist"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if sync_status column exists
            cursor.execute("PRAGMA table_info(core_responses)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'sync_status' not in columns:
                print(f"🔧 Adding sync_status column to {db_path}")
                cursor.execute("ALTER TABLE core_responses ADD COLUMN sync_status VARCHAR DEFAULT 'local_only'")
                conn.commit()
                print(f"✅ Added sync_status column to {db_path}")
            else:
                print(f"✅ sync_status column already exists in {db_path}")
            
            # Check quote_analysis table too
            cursor.execute("PRAGMA table_info(quote_analysis)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'sync_status' not in columns:
                print(f"🔧 Adding sync_status column to quote_analysis table in {db_path}")
                cursor.execute("ALTER TABLE quote_analysis ADD COLUMN sync_status VARCHAR DEFAULT 'local_only'")
                conn.commit()
                print(f"✅ Added sync_status column to quote_analysis table in {db_path}")
            else:
                print(f"✅ sync_status column already exists in quote_analysis table in {db_path}")
                
    except Exception as e:
        print(f"❌ Error fixing database schema: {e}")
        return False
    
    return True

def create_backup(db_path):
    """Create a backup of the current database"""
    backup_path = db_path + ".backup"
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return None

def ensure_correct_database():
    """Main function to ensure the correct database is used"""
    print("🔧 PRODUCTION DATABASE FIX")
    print("=" * 50)
    
    # Get the correct database path
    db_path = get_database_path()
    print(f"📁 Database path: {db_path}")
    
    # Check if database file exists
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        print("🔧 Creating new database with correct schema...")
        
        # Import and run database initialization
        try:
            from database import VOCDatabase
            db = VOCDatabase()
            print("✅ Created new database with correct schema")
        except Exception as e:
            print(f"❌ Error creating database: {e}")
            return False
    else:
        print(f"✅ Database file exists: {db_path}")
    
    # Create backup
    backup_path = create_backup(db_path)
    
    # Fix schema if needed
    if not check_database_schema(db_path):
        print("🔧 Fixing database schema...")
        if not fix_database_schema(db_path):
            print("❌ Failed to fix database schema")
            return False
    
    # Final verification
    if check_database_schema(db_path):
        print("\n✅ PRODUCTION DATABASE IS READY!")
        print(f"📊 Database: {db_path}")
        print(f"💾 Backup: {backup_path}")
        return True
    else:
        print("\n❌ DATABASE FIX FAILED!")
        return False

def show_database_info():
    """Show detailed information about the database"""
    db_path = get_database_path()
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Get table info
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            print(f"\n📊 DATABASE INFO: {db_path}")
            print("=" * 50)
            print(f"Tables: {', '.join(tables)}")
            
            # Check core_responses
            if 'core_responses' in tables:
                cursor.execute("SELECT COUNT(*) FROM core_responses")
                count = cursor.fetchone()[0]
                print(f"Records in core_responses: {count}")
                
                cursor.execute("PRAGMA table_info(core_responses)")
                columns = [row[1] for row in cursor.fetchall()]
                print(f"Columns in core_responses: {', '.join(columns)}")
            
            # Check quote_analysis
            if 'quote_analysis' in tables:
                cursor.execute("SELECT COUNT(*) FROM quote_analysis")
                count = cursor.fetchone()[0]
                print(f"Records in quote_analysis: {count}")
                
                cursor.execute("PRAGMA table_info(quote_analysis)")
                columns = [row[1] for row in cursor.fetchall()]
                print(f"Columns in quote_analysis: {', '.join(columns)}")
                
    except Exception as e:
        print(f"❌ Error getting database info: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "info":
        show_database_info()
    else:
        success = ensure_correct_database()
        if success:
            print("\n🚀 Production database is ready for use!")
            print("💡 Restart your Streamlit app to use the fixed database.")
        else:
            print("\n❌ Failed to fix production database!")
            sys.exit(1) 