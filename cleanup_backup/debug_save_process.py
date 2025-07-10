#!/usr/bin/env python3
"""
Debug the save process in Stage 4
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stage4_theme_analyzer import Stage4ThemeAnalyzer
from supabase_database import SupabaseDatabase

def debug_save_process():
    """Debug the save process in Stage 4"""
    
    print("🔍 Debugging Save Process")
    print("=" * 50)
    
    # Initialize analyzer and database
    analyzer = Stage4ThemeAnalyzer()
    db = SupabaseDatabase()
    
    # Get findings for analysis
    df = analyzer.get_findings_for_analysis(client_id='Rev')
    
    if df.empty:
        print("❌ No findings available for theme generation")
        return
    
    print(f"✅ Found {len(df)} findings for analysis")
    
    # Analyze patterns
    patterns = analyzer.analyze_finding_patterns(df, client_id='Rev')
    
    if not patterns:
        print("❌ No patterns found")
        return
    
    print(f"✅ Found {len(patterns)} patterns")
    
    # Generate theme statements
    themes = analyzer.generate_theme_statements(patterns)
    
    if not themes:
        print("❌ No themes generated")
        return
    
    print(f"✅ Generated {len(themes)} themes")
    
    # Debug each theme before saving
    for i, theme in enumerate(themes, 1):
        print(f"\n🎯 Theme {i} before save:")
        print(f"   📝 Theme statement: {theme['theme_statement'][:100]}...")
        print(f"   📝 Quotes field type: {type(theme.get('quotes'))}")
        print(f"   📝 Quotes field value: {theme.get('quotes')}")
        
        if theme.get('quotes'):
            print(f"   📄 Quotes as string: {theme['quotes'][:200]}...")
        else:
            print(f"   ❌ Quotes field is None or empty")
        
        # Check if theme would be saved
        if not theme.get('primary_theme_quote'):
            print(f"   ⚠️ This theme would be SKIPPED due to empty primary_theme_quote")
            continue
        
        print(f"   ✅ This theme would be saved")
        
        # Try to save this specific theme
        print(f"   💾 Attempting to save theme {i}...")
        
        # Add client_id
        theme['client_id'] = 'Rev'
        
        # Save the theme
        success = db.save_theme(theme)
        
        if success:
            print(f"   ✅ Theme {i} saved successfully")
            
            # Immediately retrieve it
            themes_df = db.get_themes(client_id='Rev')
            
            if not themes_df.empty:
                latest_theme = themes_df.iloc[0]
                print(f"   📖 Retrieved theme: {latest_theme['theme_statement'][:100]}...")
                
                # Check quotes field
                quotes_field = latest_theme.get('quotes')
                print(f"   📝 Retrieved quotes field type: {type(quotes_field)}")
                print(f"   📝 Retrieved quotes field value: {quotes_field}")
                
                if quotes_field:
                    if isinstance(quotes_field, list):
                        print(f"   ✅ Retrieved quotes is a list with {len(quotes_field)} items")
                    else:
                        print(f"   ❌ Retrieved quotes is not a list: {type(quotes_field)}")
                else:
                    print(f"   ❌ Retrieved quotes field is None or empty")
            else:
                print(f"   ❌ No themes found after save")
        else:
            print(f"   ❌ Failed to save theme {i}")

if __name__ == "__main__":
    debug_save_process() 