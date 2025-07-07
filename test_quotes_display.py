#!/usr/bin/env python3
"""
Test script to verify quotes display in themes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase_database import SupabaseDatabase

def test_quotes_parsing():
    """Test that quotes are being parsed correctly from themes"""
    
    print("🧪 Testing Quotes Parsing in Themes")
    print("=" * 50)
    
    # Initialize database
    db = SupabaseDatabase()
    
    # Get themes
    themes_df = db.get_themes(client_id='Rev')
    
    if themes_df.empty:
        print("❌ No themes found")
        return
    
    print(f"✅ Found {len(themes_df)} themes")
    
    # Check each theme for quotes
    for i, (_, theme) in enumerate(themes_df.iterrows(), 1):
        print(f"\n🎯 Theme {i}: {theme['theme_statement'][:100]}...")
        
        # Check if quotes field exists
        if 'quotes' in theme:
            quotes = theme['quotes']
            print(f"   📝 Quotes field type: {type(quotes)}")
            
            if isinstance(quotes, list):
                print(f"   ✅ Quotes is a list with {len(quotes)} items")
                
                if quotes:
                    print(f"   📋 First quote: {quotes[0].get('text', 'No text')[:100]}...")
                    
                    # Check quote structure
                    first_quote = quotes[0]
                    if isinstance(first_quote, dict):
                        print(f"   ✅ Quote is a dictionary with keys: {list(first_quote.keys())}")
                        
                        # Check for required fields
                        required_fields = ['text', 'impact_score', 'confidence_score', 'attribution']
                        missing_fields = [field for field in required_fields if field not in first_quote]
                        if missing_fields:
                            print(f"   ⚠️ Missing fields: {missing_fields}")
                        else:
                            print(f"   ✅ All required fields present")
                    else:
                        print(f"   ❌ Quote is not a dictionary: {type(first_quote)}")
                else:
                    print(f"   ⚠️ Quotes list is empty")
            else:
                print(f"   ❌ Quotes is not a list: {type(quotes)}")
                if isinstance(quotes, str):
                    print(f"   📄 Quotes as string: {quotes[:200]}...")
        else:
            print(f"   ❌ No 'quotes' field found in theme")
            print(f"   📋 Available fields: {list(theme.keys())}")

if __name__ == "__main__":
    test_quotes_parsing() 