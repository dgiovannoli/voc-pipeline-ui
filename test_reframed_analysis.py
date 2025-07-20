#!/usr/bin/env python3
"""
Test Reframed VOC Analysis
==========================

Test the new reframed approach that treats "no complaints" as positive
and prioritizes product complaints as improvement opportunities.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from official_scripts.reframed_voc_analyzer import ReframedVOCAnalyzer
from official_scripts.database.supabase_database import SupabaseDatabase

def test_reframed_analysis():
    """Test the reframed VOC analysis"""
    print("🎯 TESTING REFRAMED VOC ANALYSIS")
    print("=" * 50)
    
    try:
        # Initialize database and analyzer
        db = SupabaseDatabase()
        analyzer = ReframedVOCAnalyzer(db)
        
        # Run analysis
        assessment = analyzer.analyze_client_feedback("Rev")
        
        # Display results
        print(assessment.assessment_summary)
        
        # Show detailed breakdown
        print("\n📊 DETAILED BREAKDOWN:")
        print(f"Total Feedback: {assessment.problem_ratio + assessment.benefit_ratio + (1 - assessment.problem_ratio - assessment.benefit_ratio):.1%}")
        print(f"Product Complaints: {len(assessment.product_complaints)}")
        print(f"Benefit Discussions: {len(assessment.benefit_discussions)}")
        print(f"Neutral Discussions: {len(assessment.neutral_discussions)}")
        
        # Show improvement opportunities
        if assessment.improvement_opportunities:
            print(f"\n🔧 TOP IMPROVEMENT OPPORTUNITIES ({len(assessment.improvement_opportunities)}):")
            for i, opp in enumerate(assessment.improvement_opportunities[:5], 1):
                print(f"{i}. Priority {opp['priority']} - {opp['impact']} Impact")
                print(f"   Issues: {', '.join(opp['issues'])}")
                print(f"   Quote: {opp['text'][:80]}...")
                print()
        else:
            print("\n🔧 No specific improvement opportunities identified")
        
        # Show winning factors
        if assessment.winning_factors:
            print(f"\n✅ TOP WINNING FACTORS ({len(assessment.winning_factors)}):")
            for i, factor in enumerate(assessment.winning_factors[:5], 1):
                print(f"{i}. Priority {factor['priority']} - {factor['impact']} Impact")
                print(f"   Benefits: {', '.join(factor['benefits'])}")
                print(f"   Quote: {factor['text'][:80]}...")
                print()
        else:
            print("\n✅ No specific winning factors identified")
        
        # Compare with original approach
        print("\n🔄 COMPARISON WITH ORIGINAL APPROACH:")
        print("Original Score: ~4.0/10 (based on sentiment analysis)")
        print(f"Reframed Score: {assessment.overall_score}/10 (treats 'no complaints' as positive)")
        
        score_difference = assessment.overall_score - 4.0
        if score_difference > 0:
            print(f"📈 Improvement: +{score_difference:.1f} points")
            print("   This reflects that many customers aren't complaining about the product")
        elif score_difference < 0:
            print(f"📉 Difference: {score_difference:.1f} points")
            print("   This reflects more product complaints than expected")
        else:
            print("📊 No change in score")
        
        print("\n💡 KEY INSIGHT:")
        print("The reframed approach recognizes that when products work well,")
        print("customers focus on benefits and outcomes rather than the product itself.")
        print("Neutral discussions (no complaints) are treated as positive indicators.")
        
    except Exception as e:
        print(f"❌ Error running reframed analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_reframed_analysis() 