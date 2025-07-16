#!/usr/bin/env python3
"""
Test Enhanced Pipeline
Runs Stage 3 + Stage 4 with client-specific detection and enhanced structure
"""

import os
import sys
import pandas as pd
from stage3_findings_analyzer_enhanced import EnhancedStage3FindingsAnalyzer
from stage4_theme_analyzer_enhanced_structure import EnhancedStage4ThemeAnalyzer
from supabase_database import SupabaseDatabase

def test_enhanced_pipeline():
    """Test the enhanced pipeline with client-specific detection"""
    
    print("🧪 Testing Enhanced Pipeline with Client-Specific Detection")
    print("=" * 60)
    
    client_id = 'Rev'
    
    # Step 1: Run Enhanced Stage 3
    print("\n🔄 Step 1: Running Enhanced Stage 3 (with client-specific detection)...")
    stage3_analyzer = EnhancedStage3FindingsAnalyzer(client_id)
    stage3_success = stage3_analyzer.analyze_enhanced_findings()
    
    if stage3_success:
        print("✅ Enhanced Stage 3 completed successfully")
    else:
        print("❌ Enhanced Stage 3 failed")
        return False
    
    # Step 2: Run Enhanced Stage 4
    print("\n🔄 Step 2: Running Enhanced Stage 4 (with enhanced structure)...")
    stage4_analyzer = EnhancedStage4ThemeAnalyzer(client_id)
    stage4_success = stage4_analyzer.analyze_themes_enhanced_structure()
    
    if stage4_success:
        print("✅ Enhanced Stage 4 completed successfully")
    else:
        print("❌ Enhanced Stage 4 failed")
        return False
    
    # Step 3: Display Results
    print("\n📊 Step 3: Analyzing Results...")
    display_results(client_id)
    
    return True

def display_results(client_id: str):
    """Display the results of the enhanced pipeline"""
    
    db = SupabaseDatabase()
    
    # Get Stage 3 findings
    findings = db.get_stage3_findings(client_id)
    print(f"\n📋 Stage 3 Findings Summary:")
    print(f"   Total findings: {len(findings)}")
    
    # Count client-specific findings
    if 'client_specific' in findings.columns:
        client_specific_findings = findings[findings['client_specific'] == True]
        print(f"   Rev-specific findings: {len(client_specific_findings)}")
        print(f"   Market trend findings: {len(findings) - len(client_specific_findings)}")
    else:
        print(f"   Rev-specific findings: 0 (column not found)")
        print(f"   Market trend findings: {len(findings)}")
        client_specific_findings = pd.DataFrame()
    
    # Show sample Rev-specific findings
    if not client_specific_findings.empty:
        print(f"\n🔍 Sample Rev-specific findings:")
        for i, (_, finding) in enumerate(client_specific_findings.head(3).iterrows()):
            print(f"   {i+1}. {finding.get('finding_statement', '')[:100]}...")
    
    # Get Stage 4 themes
    themes = db.get_themes(client_id)
    print(f"\n🎯 Stage 4 Themes Summary:")
    print(f"   Total themes: {len(themes)}")
    
    # Count client-specific themes
    if 'client_specific' in themes.columns:
        client_specific_themes = themes[themes['client_specific'] == True]
        print(f"   Rev-specific themes: {len(client_specific_themes)}")
        print(f"   Market themes: {len(themes) - len(client_specific_themes)}")
    else:
        print(f"   Rev-specific themes: 0 (column not found)")
        print(f"   Market themes: {len(themes)}")
        client_specific_themes = pd.DataFrame()
    
    # Display themes with enhanced structure
    print(f"\n📝 Latest Themes (Enhanced Structure):")
    for i, (_, theme) in enumerate(themes.head(5).iterrows()):
        theme_type = "Rev-specific" if theme.get('client_specific', False) and 'client_specific' in themes.columns else "Market"
        print(f"\n{i+1}. [{theme_type}] {theme.get('theme_title', '')}")
        print(f"   Statement: {theme.get('theme_statement', '')[:150]}...")
        print(f"   Evidence Strength: {theme.get('theme_evidence_strength', 'N/A')}")
        if theme.get('primary_quote'):
            print(f"   Quote: {theme.get('primary_quote', '')[:100]}...")
    
    # Quality Assessment
    print(f"\n✅ Quality Assessment:")
    
    # Check theme title format
    proper_titles = 0
    for _, theme in themes.iterrows():
        title = theme.get('theme_title', '').lower()
        if any(driver in title for driver in ['frustration', 'anxiety', 'pressure', 'fatigue', 'fear']):
            if any(impact in title for impact in ['drives', 'blocks', 'creates', 'impacts', 'affects', 'jeopardizes']):
                proper_titles += 1
    
    print(f"   Themes with proper title format: {proper_titles}/{len(themes)}")
    
    # Check for quotes
    themes_with_quotes = themes[themes.get('primary_quote', '').str.len() > 10]
    print(f"   Themes with customer quotes: {len(themes_with_quotes)}/{len(themes)}")
    
    # Check for two-sentence structure
    proper_structure = 0
    for _, theme in themes.iterrows():
        statement = theme.get('theme_statement', '')
        if len(statement.split('.')) >= 2:
            proper_structure += 1
    
    print(f"   Themes with proper two-sentence structure: {proper_structure}/{len(themes)}")
    
    # Rev-specific detection success
    if len(client_specific_themes) > 0:
        print(f"   ✅ Successfully identified {len(client_specific_themes)} Rev-specific themes")
    else:
        print(f"   ⚠️  No Rev-specific themes detected - may need prompt tuning")

if __name__ == "__main__":
    success = test_enhanced_pipeline()
    
    if success:
        print(f"\n🎉 Enhanced pipeline test completed successfully!")
        print(f"   - Client-specific detection implemented")
        print(f"   - Enhanced theme structure applied")
        print(f"   - Quality validation in place")
    else:
        print(f"\n❌ Enhanced pipeline test failed")
        sys.exit(1) 