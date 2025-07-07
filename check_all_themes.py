#!/usr/bin/env python3
"""
Check all rows in the themes table, showing all fields
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase_database import SupabaseDatabase

def check_all_themes():
    print("🔍 Checking ALL rows in themes table")
    print("=" * 50)
    db = SupabaseDatabase()
    try:
        response = db.supabase.table('themes').select('*').execute()
        themes_data = response.data
        if not themes_data:
            print("❌ No themes found in database")
            return
        print(f"✅ Found {len(themes_data)} themes in database")
        for i, theme in enumerate(themes_data, 1):
            print(f"\n🎯 Theme {i}:")
            for k, v in theme.items():
                if k == 'quotes' and v:
                    if isinstance(v, str) and len(v) > 200:
                        print(f"   {k}: {v[:200]}... (truncated)")
                    else:
                        print(f"   {k}: {v}")
                else:
                    print(f"   {k}: {v}")
    except Exception as e:
        print(f"❌ Error querying database: {e}")

if __name__ == "__main__":
    check_all_themes() 