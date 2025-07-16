#!/usr/bin/env python3
"""
Compare Stage 4 Results - Original vs Two-Stage Approach
"""

import pandas as pd
from supabase_database import SupabaseDatabase
from datetime import datetime

def compare_stage4_results():
    """Compare original vs two-stage Stage 4 results"""
    
    db = SupabaseDatabase()
    
    # Get all themes for Rev client
    df = db.supabase.table('stage4_themes').select('*').eq('client_id', 'Rev').execute()
    themes = df.data
    
    if not themes:
        print("❌ No themes found")
        return
    
    print(f"📊 Total themes in database: {len(themes)}")
    
    # Sort by created_at to separate original vs v2
    themes.sort(key=lambda x: x.get('created_at', ''))
    
    # Split into original (first 21) and v2 (last 11)
    original_themes = themes[:21]
    v2_themes = themes[-11:]
    
    print(f"\n🔍 Original Approach Results:")
    print(f"   Themes: {len([t for t in original_themes if t.get('theme_type') == 'theme'])}")
    print(f"   Strategic Alerts: {len([t for t in original_themes if t.get('theme_type') == 'strategic_alert'])}")
    print(f"   Total: {len(original_themes)}")
    
    print(f"\n🚀 Two-Stage Approach Results:")
    print(f"   Themes: {len([t for t in v2_themes if t.get('theme_type') == 'theme'])}")
    print(f"   Strategic Alerts: {len([t for t in v2_themes if t.get('theme_type') == 'strategic_alert'])}")
    print(f"   Total: {len(v2_themes)}")
    
    # Compare theme quality
    print(f"\n📈 QUALITY COMPARISON:")
    
    # Original themes
    original_theme_statements = [t.get('theme_statement', '') for t in original_themes if t.get('theme_type') == 'theme']
    original_alert_statements = [t.get('alert_statement', '') for t in original_themes if t.get('theme_type') == 'strategic_alert']
    
    # V2 themes
    v2_theme_statements = [t.get('theme_statement', '') for t in v2_themes if t.get('theme_type') == 'theme']
    v2_alert_statements = [t.get('alert_statement', '') for t in v2_themes if t.get('theme_type') == 'strategic_alert']
    
    # Word count analysis
    def analyze_statements(statements, name):
        if not statements:
            return
        
        word_counts = [len(s.split()) for s in statements if s]
        cross_company_validation = sum(1 for s in statements if 'across' in s.lower() or 'spanning' in s.lower())
        solutioning_language = sum(1 for s in statements if any(word in s.lower() for word in ['indicating', 'suggesting', 'recommending', 'should', 'must']))
        
        print(f"\n{name}:")
        print(f"   Average word count: {sum(word_counts)/len(word_counts):.1f}")
        print(f"   Cross-company validation: {cross_company_validation}/{len(statements)} ({cross_company_validation/len(statements)*100:.1f}%)")
        print(f"   Solutioning language: {solutioning_language}/{len(statements)} ({solutioning_language/len(statements)*100:.1f}%)")
        
        # Show examples
        print(f"   Examples:")
        for i, statement in enumerate(statements[:3]):
            print(f"     {i+1}. {statement[:100]}...")
    
    analyze_statements(original_theme_statements, "🔍 Original Themes")
    analyze_statements(v2_theme_statements, "🚀 V2 Themes")
    analyze_statements(original_alert_statements, "🔍 Original Alerts")
    analyze_statements(v2_alert_statements, "🚀 V2 Alerts")
    
    # Cross-company validation comparison
    print(f"\n🏢 CROSS-COMPANY VALIDATION:")
    
    def count_companies(statements):
        company_counts = []
        for statement in statements:
            if 'across' in statement.lower():
                import re
                match = re.search(r'across (\d+)', statement.lower())
                if match:
                    company_counts.append(int(match.group(1)))
        return company_counts
    
    original_companies = count_companies(original_theme_statements)
    v2_companies = count_companies(v2_theme_statements)
    
    print(f"   Original average companies per theme: {sum(original_companies)/len(original_companies) if original_companies else 0:.1f}")
    print(f"   V2 average companies per theme: {sum(v2_companies)/len(v2_companies) if v2_companies else 0:.1f}")
    
    # Specificity comparison
    print(f"\n🎯 SPECIFICITY COMPARISON:")
    
    def count_specific_terms(statements):
        specific_terms = ['specific', 'concrete', 'particular', 'detailed', 'precise', 'exact']
        total_specific = 0
        for statement in statements:
            total_specific += sum(1 for term in specific_terms if term in statement.lower())
        return total_specific
    
    original_specific = count_specific_terms(original_theme_statements)
    v2_specific = count_specific_terms(v2_theme_statements)
    
    print(f"   Original specific terms: {original_specific}")
    print(f"   V2 specific terms: {v2_specific}")
    
    # Business impact comparison
    print(f"\n💼 BUSINESS IMPACT COMPARISON:")
    
    def count_business_terms(statements):
        business_terms = ['revenue', 'competitive', 'market', 'business', 'impact', 'positioning', 'advantage', 'vulnerability']
        total_business = 0
        for statement in statements:
            total_business += sum(1 for term in business_terms if term in statement.lower())
        return total_business
    
    original_business = count_business_terms(original_theme_statements)
    v2_business = count_business_terms(v2_theme_statements)
    
    print(f"   Original business terms: {original_business}")
    print(f"   V2 business terms: {v2_business}")
    
    print(f"\n📊 SUMMARY:")
    print(f"   Original approach: {len(original_themes)} themes/alerts")
    print(f"   Two-stage approach: {len(v2_themes)} themes/alerts")
    print(f"   V2 generated fewer but potentially higher quality themes")
    print(f"   Two-stage approach used GPT-4o for theme development vs GPT-4o-mini for original")

if __name__ == "__main__":
    compare_stage4_results() 