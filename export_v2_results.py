#!/usr/bin/env python3
"""
Export V2 (Two-Stage) Stage 4 Results
"""

import pandas as pd
from supabase_database import SupabaseDatabase
import json

def export_v2_results():
    """Export the V2 (two-stage) Stage 4 results"""
    
    db = SupabaseDatabase()
    
    # Get all themes for Rev client
    df = db.supabase.table('stage4_themes').select('*').eq('client_id', 'Rev').execute()
    themes = df.data
    
    if not themes:
        print("❌ No themes found")
        return
    
    # Sort by created_at to get the latest (V2) results
    themes.sort(key=lambda x: x.get('created_at', ''))
    
    # Get the last 11 themes (V2 results)
    v2_themes = themes[-11:]
    
    print(f"📊 V2 (Two-Stage) Results:")
    print(f"   Total themes/alerts: {len(v2_themes)}")
    
    # Separate themes and alerts
    v2_themes_only = [t for t in v2_themes if t.get('theme_type') == 'theme']
    v2_alerts_only = [t for t in v2_themes if t.get('theme_type') == 'strategic_alert']
    
    print(f"   Themes: {len(v2_themes_only)}")
    print(f"   Strategic Alerts: {len(v2_alerts_only)}")
    
    print(f"\n🎯 THEMES:")
    for i, theme in enumerate(v2_themes_only, 1):
        print(f"\n{i}. {theme.get('theme_title', 'N/A')}")
        print(f"   Classification: {theme.get('classification', 'N/A')}")
        print(f"   Statement: {theme.get('theme_statement', 'N/A')}")
        print(f"   Supporting Findings: {theme.get('supporting_finding_ids', 'N/A')}")
        print(f"   Companies: {theme.get('company_ids', 'N/A')}")
        if theme.get('primary_quote'):
            print(f"   Primary Quote: {theme.get('primary_quote', '')[:100]}...")
    
    print(f"\n🚨 STRATEGIC ALERTS:")
    for i, alert in enumerate(v2_alerts_only, 1):
        print(f"\n{i}. {alert.get('alert_title', 'N/A')}")
        print(f"   Classification: {alert.get('alert_classification', 'N/A')}")
        print(f"   Statement: {alert.get('alert_statement', 'N/A')}")
        print(f"   Strategic Implications: {alert.get('strategic_implications', 'N/A')}")
        print(f"   Supporting Findings: {alert.get('supporting_alert_finding_ids', 'N/A')}")
        print(f"   Companies: {alert.get('alert_company_ids', 'N/A')}")
        if alert.get('primary_alert_quote'):
            print(f"   Primary Quote: {alert.get('primary_alert_quote', '')[:100]}...")
    
    # Export to CSV for detailed analysis
    v2_df = pd.DataFrame(v2_themes)
    csv_filename = f"Context/stage4_themes_v2_results.csv"
    v2_df.to_csv(csv_filename, index=False)
    print(f"\n✅ Exported V2 results to {csv_filename}")
    
    # Quality metrics
    print(f"\n📈 V2 QUALITY METRICS:")
    
    theme_statements = [t.get('theme_statement', '') for t in v2_themes_only]
    alert_statements = [a.get('alert_statement', '') for a in v2_alerts_only]
    
    # Word count analysis
    theme_word_counts = [len(s.split()) for s in theme_statements if s]
    alert_word_counts = [len(s.split()) for s in alert_statements if s]
    
    print(f"   Theme average word count: {sum(theme_word_counts)/len(theme_word_counts):.1f}")
    print(f"   Alert average word count: {sum(alert_word_counts)/len(alert_word_counts):.1f}")
    
    # Cross-company validation
    theme_cross_company = sum(1 for s in theme_statements if 'across' in s.lower())
    alert_cross_company = sum(1 for s in alert_statements if 'across' in s.lower())
    
    print(f"   Themes with cross-company validation: {theme_cross_company}/{len(theme_statements)} ({theme_cross_company/len(theme_statements)*100:.1f}%)")
    print(f"   Alerts with cross-company validation: {alert_cross_company}/{len(alert_statements)} ({alert_cross_company/len(alert_statements)*100:.1f}%)")
    
    # Solutioning language detection
    solutioning_words = ['indicating', 'suggesting', 'recommending', 'should', 'must', 'need to']
    theme_solutioning = sum(1 for s in theme_statements if any(word in s.lower() for word in solutioning_words))
    alert_solutioning = sum(1 for s in alert_statements if any(word in s.lower() for word in solutioning_words))
    
    print(f"   Themes with solutioning language: {theme_solutioning}/{len(theme_statements)} ({theme_solutioning/len(theme_statements)*100:.1f}%)")
    print(f"   Alerts with solutioning language: {alert_solutioning}/{len(alert_statements)} ({alert_solutioning/len(alert_statements)*100:.1f}%)")
    
    # Business impact terms
    business_terms = ['revenue', 'competitive', 'market', 'business', 'impact', 'positioning', 'advantage', 'vulnerability', 'threat', 'opportunity']
    theme_business_terms = sum(sum(1 for term in business_terms if term in s.lower()) for s in theme_statements)
    alert_business_terms = sum(sum(1 for term in business_terms if term in s.lower()) for s in alert_statements)
    
    print(f"   Business impact terms in themes: {theme_business_terms}")
    print(f"   Business impact terms in alerts: {alert_business_terms}")

if __name__ == "__main__":
    export_v2_results() 