#!/usr/bin/env python3
"""
Check what's actually stored in the themes table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase_database import SupabaseDatabase

def check_database_quotes():
    """Check what's actually stored in the themes table"""
    
    print("🔍 Checking Database Themes Table")
    print("=" * 50)
    
    # Initialize database
    db = SupabaseDatabase()
    
    # Get themes directly from database
    try:
        response = db.supabase.table('stage4_themes').select('*').eq('client_id', 'Rev').order('created_at', desc=True).execute()
        themes_data = response.data
        
        if not themes_data:
            print("❌ No themes found in database")
            return
        
        print(f"✅ Found {len(themes_data)} themes in database")
        
        # Check each theme
        for i, theme in enumerate(themes_data, 1):
            print(f"\n🎯 Theme {i}: {theme.get('theme_statement', 'No statement')[:100]}...")
            
            # Check quotes field
            quotes_field = theme.get('quotes')
            print(f"   📝 Quotes field type: {type(quotes_field)}")
            print(f"   📝 Quotes field value: {quotes_field}")
            
            if quotes_field:
                if isinstance(quotes_field, str):
                    print(f"   📄 Quotes as string: {quotes_field[:200]}...")
                else:
                    print(f"   📄 Quotes as other type: {quotes_field}")
            else:
                print(f"   ❌ Quotes field is None or empty")
            
            # Check other fields
            print(f"   📊 Theme strength: {theme.get('theme_strength')}")
            print(f"   📊 Theme category: {theme.get('theme_category')}")
            print(f"   📊 Primary quote: {theme.get('primary_theme_quote', 'None')[:100]}...")
            
    except Exception as e:
        print(f"❌ Error querying database: {e}")

if __name__ == "__main__":
    check_database_quotes() 