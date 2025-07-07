#!/usr/bin/env python3
"""
Test script to verify quote validation fixes in Stage 3 and Stage 4
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stage3_findings_analyzer import run_stage3_analysis
from stage4_theme_analyzer import run_stage4_analysis
from supabase_database import SupabaseDatabase

def test_quote_validation():
    """Test that both Stage 3 and Stage 4 properly validate quotes"""
    
    print("🧪 Testing Quote Validation Fixes")
    print("=" * 50)
    
    # Test Stage 3
    print("\n📊 Testing Stage 3 - Enhanced Findings...")
    stage3_result = run_stage3_analysis('Rev')
    
    if stage3_result['status'] == 'success':
        print(f"✅ Stage 3 completed successfully")
        print(f"   - Findings generated: {stage3_result.get('findings_generated', 0)}")
        
        # Check if findings have quotes
        db = SupabaseDatabase()
        findings = db.get_enhanced_findings('Rev')
        
        findings_with_quotes = 0
        findings_without_quotes = 0
        
        for _, finding in findings.iterrows():
            selected_quotes = finding.get('selected_quotes', [])
            if selected_quotes and len(selected_quotes) > 0:
                findings_with_quotes += 1
            else:
                findings_without_quotes += 1
        
        print(f"   - Findings with quotes: {findings_with_quotes}")
        print(f"   - Findings without quotes: {findings_without_quotes}")
        
        if findings_without_quotes == 0:
            print("✅ Stage 3 validation working correctly - all findings have quotes!")
        else:
            print("⚠️ Stage 3 validation issue - some findings missing quotes")
    else:
        print(f"❌ Stage 3 failed: {stage3_result}")
    
    # Test Stage 4
    print("\n🎯 Testing Stage 4 - Theme Generation...")
    stage4_result = run_stage4_analysis('Rev')
    
    if stage4_result['status'] == 'success':
        print(f"✅ Stage 4 completed successfully")
        print(f"   - Themes generated: {stage4_result.get('themes_generated', 0)}")
        
        # Check if themes have quotes
        themes = db.get_themes('Rev')
        
        themes_with_quotes = 0
        themes_without_quotes = 0
        
        for _, theme in themes.iterrows():
            primary_quote = theme.get('primary_theme_quote', '')
            if primary_quote and len(primary_quote.strip()) > 0:
                themes_with_quotes += 1
            else:
                themes_without_quotes += 1
        
        print(f"   - Themes with quotes: {themes_with_quotes}")
        print(f"   - Themes without quotes: {themes_without_quotes}")
        
        if themes_without_quotes == 0:
            print("✅ Stage 4 validation working correctly - all themes have quotes!")
        else:
            print("⚠️ Stage 4 validation issue - some themes missing quotes")
    else:
        print(f"❌ Stage 4 failed: {stage4_result}")
    
    print("\n🎉 Quote validation test complete!")

if __name__ == "__main__":
    test_quote_validation() 