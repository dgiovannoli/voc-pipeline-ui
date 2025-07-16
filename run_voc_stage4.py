#!/usr/bin/env python3
"""
Runner for Voice of Customer Stage 4 Analysis
"""

import os
import sys
from stage4_theme_analyzer_voc_format import VoiceOfCustomerStage4Analyzer

def main():
    """Run Voice of Customer Stage 4 analysis"""
    print("🎯 Voice of Customer Stage 4 Theme Analysis")
    print("=" * 50)
    
    # Initialize analyzer
    try:
        analyzer = VoiceOfCustomerStage4Analyzer("Rev")
        print("✅ Analyzer initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing analyzer: {e}")
        return False
    
    # Run analysis
    try:
        success = analyzer.analyze_themes_voc_format()
        
        if success:
            print("\n✅ Voice of Customer Stage 4 analysis completed successfully")
            print("\n📊 Results:")
            print("- Themes generated in VOC format")
            print("- Customer quotes mapped to primary_quote field")
            print("- Research analysis mapped to theme_statement field")
            print("- Strategic implications mapped to strategic_implications field")
            print("\n💡 The new format provides:")
            print("- Direct customer voice through quotes")
            print("- Neutral, research-based analysis")
            print("- Clear strategic implications")
            print("- Professional presentation for executives")
        else:
            print("❌ Voice of Customer Stage 4 analysis failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 