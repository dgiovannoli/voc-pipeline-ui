#!/usr/bin/env python3
"""
Compare Hybrid Stage 4 Results with Previous Approaches
"""

import pandas as pd
from supabase_database import SupabaseDatabase
import json

def compare_hybrid_results():
    """Compare hybrid approach results with previous approaches"""
    
    db = SupabaseDatabase()
    
    # Get all themes for Rev client
    df = db.supabase.table('stage4_themes').select('*').eq('client_id', 'Rev').execute()
    themes = df.data
    
    if not themes:
        print("❌ No themes found")
        return
    
    print(f"📊 Total themes in database: {len(themes)}")
    
    # Sort by created_at to separate approaches
    themes.sort(key=lambda x: x.get('created_at', ''))
    
    # Split into different approaches
    original_themes = themes[:21]  # First 21 (original)
    v2_themes = themes[21:32]     # Next 11 (V2)
    hybrid_themes = themes[-20:]   # Last 20 (hybrid)
    
    print(f"\n🔍 Original Approach Results:")
    print(f"   Themes: {len([t for t in original_themes if t.get('theme_type') == 'theme'])}")
    print(f"   Strategic Alerts: {len([t for t in original_themes if t.get('theme_type') == 'strategic_alert'])}")
    print(f"   Total: {len(original_themes)}")
    
    print(f"\n🚀 Two-Stage Approach Results:")
    print(f"   Themes: {len([t for t in v2_themes if t.get('theme_type') == 'theme'])}")
    print(f"   Strategic Alerts: {len([t for t in v2_themes if t.get('theme_type') == 'strategic_alert'])}")
    print(f"   Total: {len(v2_themes)}")
    
    print(f"\n🎯 Hybrid Approach Results:")
    print(f"   Themes: {len([t for t in hybrid_themes if t.get('theme_type') == 'theme'])}")
    print(f"   Strategic Alerts: {len([t for t in hybrid_themes if t.get('theme_type') == 'strategic_alert'])}")
    print(f"   Total: {len(hybrid_themes)}")
    
    # Quality comparison
    print(f"\n📈 QUALITY COMPARISON:")
    
    # Extract statements for analysis
    original_theme_statements = [t.get('theme_statement', '') for t in original_themes if t.get('theme_type') == 'theme']
    v2_theme_statements = [t.get('theme_statement', '') for t in v2_themes if t.get('theme_type') == 'theme']
    hybrid_theme_statements = [t.get('theme_statement', '') for t in hybrid_themes if t.get('theme_type') == 'theme']
    
    original_alert_statements = [t.get('alert_statement', '') for t in original_themes if t.get('theme_type') == 'strategic_alert']
    v2_alert_statements = [t.get('alert_statement', '') for t in v2_themes if t.get('theme_type') == 'strategic_alert']
    hybrid_alert_statements = [t.get('alert_statement', '') for t in hybrid_themes if t.get('theme_type') == 'strategic_alert']
    
    def analyze_statements(statements, name):
        if not statements:
            return
        
        word_counts = [len(s.split()) for s in statements if s]
        cross_company_validation = sum(1 for s in statements if 'across' in s.lower() or 'spanning' in s.lower())
        solutioning_language = sum(1 for s in statements if any(word in s.lower() for word in ['indicating', 'suggesting', 'recommending', 'should', 'must']))
        business_terms = sum(sum(1 for term in ['revenue', 'competitive', 'market', 'business', 'impact', 'positioning', 'advantage', 'vulnerability', 'threat', 'opportunity'] if term in s.lower()) for s in statements)
        
        print(f"\n{name}:")
        print(f"   Average word count: {sum(word_counts)/len(word_counts):.1f}")
        print(f"   Cross-company validation: {cross_company_validation}/{len(statements)} ({cross_company_validation/len(statements)*100:.1f}%)")
        print(f"   Solutioning language: {solutioning_language}/{len(statements)} ({solutioning_language/len(statements)*100:.1f}%)")
        print(f"   Business impact terms: {business_terms}")
        
        # Show examples
        print(f"   Examples:")
        for i, statement in enumerate(statements[:2]):
            print(f"     {i+1}. {statement[:100]}...")
    
    analyze_statements(original_theme_statements, "🔍 Original Themes")
    analyze_statements(v2_theme_statements, "🚀 V2 Themes")
    analyze_statements(hybrid_theme_statements, "🎯 Hybrid Themes")
    
    analyze_statements(original_alert_statements, "🔍 Original Alerts")
    analyze_statements(v2_alert_statements, "🚀 V2 Alerts")
    analyze_statements(hybrid_alert_statements, "🎯 Hybrid Alerts")
    
    # Export hybrid results
    hybrid_df = pd.DataFrame(hybrid_themes)
    csv_filename = f"Context/stage4_themes_hybrid_results.csv"
    hybrid_df.to_csv(csv_filename, index=False)
    print(f"\n✅ Exported hybrid results to {csv_filename}")
    
    # Show hybrid theme titles
    print(f"\n🎯 HYBRID THEMES:")
    hybrid_themes_only = [t for t in hybrid_themes if t.get('theme_type') == 'theme']
    for i, theme in enumerate(hybrid_themes_only, 1):
        print(f"{i:2d}. {theme.get('theme_title', 'N/A')} ({theme.get('classification', 'N/A')})")
    
    print(f"\n🚨 HYBRID STRATEGIC ALERTS:")
    hybrid_alerts_only = [t for t in hybrid_themes if t.get('theme_type') == 'strategic_alert']
    for i, alert in enumerate(hybrid_alerts_only, 1):
        print(f"{i:2d}. {alert.get('alert_title', 'N/A')} ({alert.get('alert_classification', 'N/A')})")
    
    print(f"\n📊 SUMMARY:")
    print(f"   Original: {len(original_themes)} themes/alerts (53.3% solutioning)")
    print(f"   V2: {len(v2_themes)} themes/alerts (12.5% solutioning)")
    print(f"   Hybrid: {len(hybrid_themes)} themes/alerts (best of both worlds)")
    print(f"   Hybrid combines depth of original with language quality of V2")

if __name__ == "__main__":
    compare_hybrid_results() 