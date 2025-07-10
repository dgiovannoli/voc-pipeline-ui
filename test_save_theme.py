#!/usr/bin/env python3
"""
Test saving a theme with quotes directly
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase_database import SupabaseDatabase

def test_save_theme():
    """Test saving a theme with quotes directly"""
    
    print("🧪 Testing Theme Save with Quotes")
    print("=" * 50)
    
    # Initialize database
    db = SupabaseDatabase()
    
    # Create a test theme with quotes
    test_quotes = [
        {
            "text": "This is a test quote for debugging",
            "impact_score": 4.0,
            "confidence_score": 8.0,
            "attribution": "Test Company - John Doe"
        },
        {
            "text": "This is another test quote",
            "impact_score": 3.0,
            "confidence_score": 7.0,
            "attribution": "Test Company - Jane Smith"
        }
    ]
    
    test_theme = {
        'theme_statement': 'Test theme for debugging quotes',
        'theme_category': 'Strategic',
        'theme_strength': 'Medium',
        'interview_companies': ['Test Company'],
        'supporting_finding_ids': [1, 2],
        'supporting_response_ids': [],
        'deal_status_distribution': {"won": 1, "lost": 0},
        'competitive_flag': False,
        'business_implications': 'Test implications',
        'primary_theme_quote': 'This is a test quote',
        'secondary_theme_quote': 'This is another test quote',
        'quote_attributions': 'Test Company',
        'evidence_strength': 'Medium',
        'avg_confidence_score': 7.5,
        'company_count': 1,
        'finding_count': 2,
        'quotes': json.dumps(test_quotes)  # Save as JSON string
    }
    
    print(f"📝 Test theme quotes: {test_quotes}")
    print(f"📄 Quotes as JSON: {test_theme['quotes']}")
    
    # Save the theme
    print("\n💾 Saving test theme...")
    success = db.save_theme(test_theme, client_id='Rev')
    
    if success:
        print("✅ Theme saved successfully")
        
        # Immediately retrieve it
        print("\n📖 Retrieving saved theme...")
        stage4_themes_df = db.get_stage4_themes(client_id='Rev')
        
        if not stage4_themes_df.empty:
            latest_theme = stage4_themes_df.iloc[0]
            print(f"✅ Retrieved theme: {latest_theme['theme_statement']}")
            
            # Check quotes field
            quotes_field = latest_theme.get('quotes')
            print(f"📝 Quotes field type: {type(quotes_field)}")
            print(f"📝 Quotes field value: {quotes_field}")
            
            if quotes_field:
                if isinstance(quotes_field, list):
                    print(f"✅ Quotes is a list with {len(quotes_field)} items")
                    for i, quote in enumerate(quotes_field):
                        print(f"   📋 Quote {i+1}: {quote}")
                else:
                    print(f"❌ Quotes is not a list: {type(quotes_field)}")
            else:
                print(f"❌ Quotes field is None or empty")
        else:
            print("❌ No stage4_themes found after save")
    else:
        print("❌ Failed to save theme")

if __name__ == "__main__":
    test_save_theme() 