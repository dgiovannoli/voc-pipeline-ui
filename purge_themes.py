#!/usr/bin/env python3
"""
Purge all themes for client_id='Rev' from the Supabase database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase_database import SupabaseDatabase

def purge_themes():
    print("⚠️  Purging all themes for client_id='Rev'...")
    db = SupabaseDatabase()
    try:
        response = db.supabase.table('stage4_themes').delete().eq('client_id', 'Rev').execute()
        print(f"✅ Deleted themes for client_id='Rev'. Response: {response}")
    except Exception as e:
        print(f"❌ Error deleting themes: {e}")

if __name__ == "__main__":
    purge_themes() 