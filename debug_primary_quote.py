#!/usr/bin/env python3
"""
Debug primary quote extraction in Stage 4
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stage4_theme_analyzer import Stage4ThemeAnalyzer

def debug_primary_quote():
    """Debug primary quote extraction"""
    
    print("🔍 Debugging Primary Quote Extraction")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = Stage4ThemeAnalyzer()
    
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
    
    # Check each pattern for quotes and primary quote extraction
    for criterion, pattern in patterns.items():
        print(f"\n🎯 Pattern: {criterion}")
        
        # Check quotes
        quotes = pattern.get('quotes', [])
        print(f"   📝 Quotes count: {len(quotes)}")
        
        if quotes:
            print(f"   ✅ Quotes found!")
            
            # Check first quote structure
            first_quote = quotes[0]
            print(f"   📋 First quote type: {type(first_quote)}")
            print(f"   📋 First quote: {first_quote}")
            
            if isinstance(first_quote, dict):
                print(f"   📊 First quote keys: {list(first_quote.keys())}")
                quote_text = first_quote.get('text', '')
                print(f"   📄 Quote text: {quote_text[:100]}...")
                print(f"   📄 Quote text length: {len(quote_text)}")
                
                # Simulate primary quote extraction
                primary_quote_text = ""
                if quotes:
                    primary_quote = quotes[0]
                    if isinstance(primary_quote, dict):
                        primary_quote_text = primary_quote.get('text', '')
                    else:
                        primary_quote_text = str(primary_quote)
                
                print(f"   🎯 Extracted primary quote text: {primary_quote_text[:100]}...")
                print(f"   🎯 Primary quote text length: {len(primary_quote_text)}")
                print(f"   🎯 Primary quote text is empty: {not primary_quote_text}")
            else:
                print(f"   ❌ First quote is not a dictionary")
        else:
            print(f"   ❌ No quotes found in pattern")
    
    # Generate theme statements to see what gets created
    print(f"\n📝 Generating theme statements...")
    themes = analyzer.generate_theme_statements(patterns)
    
    if themes:
        print(f"✅ Generated {len(themes)} themes")
        
        for i, theme in enumerate(themes, 1):
            print(f"\n🎯 Theme {i}: {theme['theme_statement'][:100]}...")
            
            # Check primary quote field
            primary_quote = theme.get('primary_theme_quote', '')
            print(f"   🎯 Primary theme quote: {primary_quote[:100]}...")
            print(f"   🎯 Primary quote length: {len(primary_quote)}")
            print(f"   🎯 Primary quote is empty: {not primary_quote}")
            
            # Check quotes field
            quotes_field = theme.get('quotes', '')
            print(f"   📝 Quotes field: {quotes_field[:200]}...")
            
            # Check if theme would be saved
            if not primary_quote:
                print(f"   ⚠️ This theme would be SKIPPED due to empty primary_theme_quote")
            else:
                print(f"   ✅ This theme would be saved")

if __name__ == "__main__":
    debug_primary_quote() 