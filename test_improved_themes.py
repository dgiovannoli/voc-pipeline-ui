#!/usr/bin/env python3

"""
Test script for improved Stage 4 theme generation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stage4_theme_analyzer import run_stage4_analysis
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_improved_theme_generation():
    """Test the improved theme generation with better prompts and quality controls"""
    
    print("🔍 Testing Improved Stage 4 Theme Generation")
    print("=" * 60)
    
    # Run Stage 4 analysis
    result = run_stage4_analysis(client_id='Rev')
    
    print(f"\n📊 Results:")
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Themes Generated: {result.get('themes_generated', 0)}")
    print(f"Findings Processed: {result.get('findings_processed', 0)}")
    
    if result.get('status') == 'success':
        print(f"High Strength Themes: {result.get('high_strength_themes', 0)}")
        print(f"Competitive Themes: {result.get('competitive_themes', 0)}")
        
        # Print summary if available
        summary = result.get('summary', {})
        if summary:
            print(f"\n📈 Theme Distribution:")
            for strength, count in summary.get('strength_distribution', {}).items():
                print(f"  {strength}: {count}")
            
            print(f"\n🎯 Category Distribution:")
            for category, count in summary.get('category_distribution', {}).items():
                print(f"  {category}: {count}")
    
    print(f"\n✅ Test complete!")
    return result

if __name__ == "__main__":
    test_improved_theme_generation() 