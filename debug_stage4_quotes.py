#!/usr/bin/env python3
"""
Debug script to check quotes during Stage 4 analysis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stage4_theme_analyzer import Stage4ThemeAnalyzer

def debug_stage4_quotes():
    """Debug quotes during Stage 4 analysis"""
    
    print("🔍 Debugging Stage 4 Quotes")
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
    
    # Check each pattern for quotes
    for criterion, pattern in patterns.items():
        print(f"\n🎯 Pattern: {criterion}")
        print(f"   📊 Company count: {pattern['company_count']}")
        print(f"   📊 Finding count: {pattern['finding_count']}")
        print(f"   📊 Avg impact score: {pattern['avg_impact_score']:.2f}")
        
        # Check quotes
        quotes = pattern.get('quotes', [])
        print(f"   📝 Quotes count: {len(quotes)}")
        
        if quotes:
            print(f"   ✅ Quotes found!")
            for i, quote in enumerate(quotes[:2]):  # Show first 2 quotes
                if isinstance(quote, dict):
                    print(f"   📋 Quote {i+1}: {quote.get('text', 'No text')[:100]}...")
                    print(f"   📊 Quote keys: {list(quote.keys())}")
                else:
                    print(f"   📋 Quote {i+1}: {str(quote)[:100]}...")
        else:
            print(f"   ❌ No quotes found in pattern")
    
    # Generate theme statements to see what gets saved
    print(f"\n📝 Generating theme statements...")
    themes = analyzer.generate_theme_statements(patterns)
    
    if themes:
        print(f"✅ Generated {len(themes)} themes")
        
        for i, theme in enumerate(themes, 1):
            print(f"\n🎯 Theme {i}: {theme['theme_statement'][:100]}...")
            
            # Check quotes field in theme
            quotes_field = theme.get('quotes', 'No quotes field')
            print(f"   📝 Quotes field: {quotes_field}")
            
            if quotes_field and quotes_field != 'No quotes field':
                if isinstance(quotes_field, str):
                    print(f"   📄 Quotes as string: {quotes_field[:200]}...")
                else:
                    print(f"   📄 Quotes type: {type(quotes_field)}")
            else:
                print(f"   ❌ No quotes in theme")

if __name__ == "__main__":
    debug_stage4_quotes() 