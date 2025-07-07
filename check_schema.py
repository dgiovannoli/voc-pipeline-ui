#!/usr/bin/env python3
"""
Check database schema for themes table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase_database import SupabaseDatabase

def check_schema():
    """Check the database schema for themes table"""
    
    print("🔍 Checking Database Schema")
    print("=" * 50)
    
    # Initialize database
    db = SupabaseDatabase()
    
    try:
        # Try to get schema information
        # Note: Supabase doesn't expose schema introspection easily
        # So we'll try to insert a test record and see what happens
        
        print("📋 Testing schema with a simple insert...")
        
        # Create a minimal test theme
        test_theme = {
            'theme_statement': 'Schema test theme',
            'theme_category': 'Strategic',
            'theme_strength': 'Medium',
            'interview_companies': ['Test Company'],
            'supporting_finding_ids': [1],
            'supporting_response_ids': [],
            'deal_status_distribution': {"won": 1, "lost": 0},
            'competitive_flag': False,
            'business_implications': 'Test implications',
            'primary_theme_quote': 'Test quote',
            'secondary_theme_quote': 'Test quote 2',
            'quote_attributions': 'Test Company',
            'evidence_strength': 'Medium',
            'avg_confidence_score': 7.0,
            'company_count': 1,
            'finding_count': 1,
            'quotes': '[{"text": "test quote", "score": 4.0}]'  # Simple JSON string
        }
        
        # Try to save
        success = db.save_theme(test_theme, client_id='Rev')
        
        if success:
            print("✅ Test theme saved successfully")
            
            # Immediately retrieve it
            themes_df = db.get_themes(client_id='Rev')
            
            if not themes_df.empty:
                latest_theme = themes_df.iloc[0]
                print(f"✅ Retrieved test theme: {latest_theme['theme_statement']}")
                
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
                print("❌ No themes found after save")
        else:
            print("❌ Failed to save test theme")
            
    except Exception as e:
        print(f"❌ Error testing schema: {e}")
        print(f"Error type: {type(e)}")
        
        # Try to get more specific error information
        if hasattr(e, 'response'):
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")

if __name__ == "__main__":
    check_schema() 