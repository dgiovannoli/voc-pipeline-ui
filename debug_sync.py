#!/usr/bin/env python3
"""
Debug script to test the sync_status error
"""

import sqlite3
import traceback
from supabase_integration import HybridDatabaseManager

def test_sync_status():
    """Test the sync status function and catch any errors"""
    try:
        print("🔍 Testing HybridDatabaseManager initialization...")
        db_manager = HybridDatabaseManager()
        print("✅ HybridDatabaseManager initialized successfully")
        
        print("🔍 Testing get_sync_status...")
        status = db_manager.get_sync_status()
        print("✅ get_sync_status completed successfully")
        print(f"Status: {status}")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        print("🔍 Full traceback:")
        traceback.print_exc()
        
        # Let's also test the database directly
        print("\n🔍 Testing database directly...")
        try:
            with sqlite3.connect("voc_pipeline.db") as conn:
                cursor = conn.cursor()
                
                # Test core_responses
                print("Testing core_responses table...")
                cursor.execute("SELECT sync_status, COUNT(*) FROM core_responses GROUP BY sync_status")
                result = cursor.fetchall()
                print(f"core_responses sync_status: {result}")
                
                # Test quote_analysis
                print("Testing quote_analysis table...")
                cursor.execute("SELECT sync_status, COUNT(*) FROM quote_analysis GROUP BY sync_status")
                result = cursor.fetchall()
                print(f"quote_analysis sync_status: {result}")
                
        except Exception as db_error:
            print(f"❌ Database error: {db_error}")
            traceback.print_exc()

if __name__ == "__main__":
    test_sync_status() 