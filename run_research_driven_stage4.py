#!/usr/bin/env python3
"""
Research-Driven Stage 4 Runner
Tests the new research-driven approach to theme generation
"""

import os
import sys
from stage4_theme_analyzer_research_driven import ResearchDrivenStage4Analyzer

def main():
    """Run research-driven Stage 4 analysis"""
    print("🎯 Research-Driven Stage 4 Theme Analysis")
    print("=" * 50)
    
    # Initialize analyzer
    try:
        analyzer = ResearchDrivenStage4Analyzer(client_id="Rev")
        print("✅ Analyzer initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing analyzer: {e}")
        return False
    
    # Run analysis
    try:
        success = analyzer.analyze_themes_research_driven()
        
        if success:
            print("\n✅ Research-driven Stage 4 analysis completed successfully!")
            print("\n📊 Key Benefits of Research-Driven Approach:")
            print("   - Data-determined theme count (not arbitrary)")
            print("   - Pattern density analysis")
            print("   - Quality-based thresholds")
            print("   - Cross-company validation requirements")
            print("   - Business impact focus")
        else:
            print("\n❌ Research-driven Stage 4 analysis failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 