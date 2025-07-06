#!/usr/bin/env python3

"""
Stage 5: Executive Synthesis Runner
Generates executive-ready themes with criteria scorecard integration
"""

import sys
import os
from stage5_executive_analyzer import run_stage5_analysis

def main():
    print("🎯 Stage 5: Executive Synthesis")
    print("=" * 50)
    print("Generating executive synthesis with criteria scorecard...")
    print()
    
    try:
        result = run_stage5_analysis()
        
        if result["status"] == "success":
            print("✅ Stage 5 completed successfully!")
            print(f"📊 Executive themes generated: {result['executive_themes_generated']}")
            print(f"🏆 High impact themes: {result['high_impact_themes']}")
            print(f"🏅 Competitive themes: {result['competitive_themes']}")
            print(f"📋 Criteria analyzed: {result['criteria_analyzed']}")
            
            # Show summary statistics
            summary = result.get('summary', {})
            if summary:
                print(f"\n📈 SUMMARY STATISTICS:")
                print(f"Total executive themes: {summary.get('total_executive_themes', 0)}")
                print(f"Average priority score: {summary.get('average_priority_score', 0)}")
                print(f"Overall criteria performance: {summary.get('overall_criteria_performance', 'N/A')}")
                print(f"Total criteria analyzed: {summary.get('total_criteria_analyzed', 0)}")
                
                # Show impact distribution
                impact_dist = summary.get('impact_distribution', {})
                if impact_dist:
                    print(f"\n🎯 Business Impact Distribution:")
                    for impact, count in impact_dist.items():
                        print(f"  {impact}: {count}")
                
                # Show readiness distribution
                readiness_dist = summary.get('readiness_distribution', {})
                if readiness_dist:
                    print(f"\n📋 Executive Readiness Distribution:")
                    for readiness, count in readiness_dist.items():
                        print(f"  {readiness}: {count}")
        else:
            print(f"⚠️ Stage 5 completed with status: {result['status']}")
            print(f"📝 Message: {result.get('message', 'No message provided')}")
            
    except Exception as e:
        print(f"❌ Error running Stage 5: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 