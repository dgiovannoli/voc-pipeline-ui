#!/usr/bin/env python3

"""
Test script for improved Stage 4 theme generation with stricter quality controls
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stage4_theme_analyzer import run_stage4_analysis
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_improved_theme_quality():
    """Test the improved theme generation with stricter quality controls"""
    
    print("🔍 Testing Improved Stage 4 Theme Generation with Stricter Quality Controls")
    print("=" * 80)
    
    # Run Stage 4 analysis with improved prompts and stricter thresholds
    result = run_stage4_analysis(client_id='Rev')
    
    print(f"\n📊 Results Summary:")
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Themes Generated: {result.get('themes_generated', 0)}")
    print(f"Themes Saved: {result.get('themes_saved', 0)}")
    print(f"Processing Time: {result.get('processing_time', 0):.2f} seconds")
    
    if result.get('themes'):
        print(f"\n🎯 Generated Themes:")
        for i, theme in enumerate(result['themes'], 1):
            print(f"\n{i}. {theme.get('theme_statement', 'N/A')}")
            print(f"   Category: {theme.get('theme_category', 'N/A')}")
            print(f"   Strength: {theme.get('theme_strength', 'N/A')}")
            print(f"   Companies: {len(theme.get('interview_companies', []))}")
            print(f"   Findings: {len(theme.get('supporting_finding_ids', []))}")
            print(f"   Impact Score: {theme.get('business_implications', 'N/A')}")
    
    if result.get('errors'):
        print(f"\n❌ Errors:")
        for error in result['errors']:
            print(f"  - {error}")
    
    print(f"\n✅ Test completed!")
    return result

if __name__ == "__main__":
    test_improved_theme_quality() 