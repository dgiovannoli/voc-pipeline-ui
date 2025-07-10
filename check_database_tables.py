#!/usr/bin/env python3
"""
Check what tables exist in the database.
"""

import os
from dotenv import load_dotenv
from supabase_database import SupabaseDatabase

def check_database_tables():
    """Check what tables exist in the database."""
    print("🔍 Checking database tables...")
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize database connection
        db = SupabaseDatabase()
        print("✅ Connected to Supabase database")
        
        # Try to get themes from stage4_themes
        try:
            themes = db.supabase.table('stage4_themes').select('*').limit(1).execute()
            print("✅ stage4_themes table exists")
            if themes.data:
                print(f"   Columns: {list(themes.data[0].keys())}")
        except Exception as e:
            print(f"❌ stage4_themes table error: {e}")
        
        # Try to get quotes from quote_analysis
        try:
            quotes = db.supabase.table('quote_analysis').select('*').limit(1).execute()
            print("✅ quote_analysis table exists")
            if quotes.data:
                print(f"   Columns: {list(quotes.data[0].keys())}")
        except Exception as e:
            print(f"❌ quote_analysis table error: {e}")
        
        # Try other possible quote table names
        possible_quote_tables = ['quotes', 'stage2_quotes', 'quote_data', 'response_quotes']
        for table_name in possible_quote_tables:
            try:
                result = db.supabase.table(table_name).select('*').limit(1).execute()
                print(f"✅ {table_name} table exists")
                if result.data:
                    print(f"   Columns: {list(result.data[0].keys())}")
            except Exception as e:
                print(f"❌ {table_name} table does not exist")
        
        # List all tables in the database
        print("\n📋 All tables in database:")
        try:
            # This might not work with Supabase, but worth trying
            result = db.supabase.rpc('get_tables').execute()
            print(result.data)
        except:
            print("Could not list all tables automatically")
            print("Please check your Supabase dashboard for table names")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    check_database_tables() 