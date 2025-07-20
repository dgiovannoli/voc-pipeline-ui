"""
Test script for Stage 2 Integrated Theme Generation
Demonstrates improvement-focused themes using Stage 2 enriched data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from official_scripts.stage2_integrated_theme_generator import Stage2IntegratedThemeGenerator

def test_stage2_integrated_themes():
    """
    Test the Stage 2 integrated theme generation
    """
    print("🎯 TESTING STAGE 2 INTEGRATED THEME GENERATION")
    print("=" * 70)
    
    # Initialize theme generator
    theme_generator = Stage2IntegratedThemeGenerator()
    
    # Generate improvement-focused themes for Rev
    result = theme_generator.generate_improvement_focused_themes('Rev')
    
    # Display results
    print(f"\n📊 DATA SUMMARY:")
    print(f"   Stage 1 Quotes: {result['data_summary']['stage1_quotes']}")
    print(f"   Stage 2 Analyses: {result['data_summary']['stage2_analyses']}")
    print(f"   Enriched Quotes: {result['data_summary']['enriched_quotes']}")
    print(f"   Criteria Analyzed: {result['data_summary']['criteria_analyzed']}")
    
    # Overall assessment
    overall = result['overall_assessment']
    print(f"\n🎯 OVERALL ASSESSMENT:")
    print(f"   Overall Score: {overall['overall_score']}/10")
    print(f"   Performance Level: {overall['performance_level']}")
    print(f"   Description: {overall['description']}")
    
    # Improvement priorities
    print(f"\n📈 TOP IMPROVEMENT PRIORITIES:")
    for i, improvement in enumerate(overall['improvement_priorities'][:3], 1):
        print(f"   {i}. {improvement['opportunity']}")
        print(f"      Criterion: {improvement['criterion']}")
        print(f"      Evidence: {improvement['evidence'][:100]}...")
        print(f"      Source: {improvement['interviewee']} at {improvement['company']}")
        print(f"      Priority Score: {improvement['priority_score']:.1f}")
        print(f"      Business Impact: {improvement['business_impact']}")
        print()
    
    # Winning highlights
    print(f"🏆 TOP WINNING HIGHLIGHTS:")
    for i, win in enumerate(overall['winning_highlights'][:3], 1):
        print(f"   {i}. {win['factor']}")
        print(f"      Criterion: {win['criterion']}")
        print(f"      Evidence: {win['evidence'][:100]}...")
        print(f"      Source: {win['interviewee']} at {win['company']}")
        print(f"      Priority Score: {win['priority_score']:.1f}")
        print(f"      Business Impact: {win['business_impact']}")
        print()
    
    # Detailed analysis by criterion
    print(f"\n🔍 DETAILED ANALYSIS BY CRITERION:")
    for criterion, theme in result['themes_by_criterion'].items():
        print(f"\n📋 {criterion.upper()}:")
        print(f"   Holistic Score: {theme['holistic_score']}/10")
        print(f"   Performance: {theme['performance_assessment']['level']}")
        
        # Improvement opportunities
        if theme['improvement_opportunities']:
            print(f"   📉 Improvement Opportunities ({len(theme['improvement_opportunities'])}):")
            for j, opp in enumerate(theme['improvement_opportunities'][:2], 1):
                print(f"      {j}. {opp['opportunity']}")
                print(f"         Evidence: {opp['evidence'][:80]}...")
                print(f"         Priority: {opp['priority_score']:.1f}, Impact: {opp['business_impact']}")
        
        # Winning factors
        if theme['winning_factors']:
            print(f"   🏆 Winning Factors ({len(theme['winning_factors'])}):")
            for j, win in enumerate(theme['winning_factors'][:2], 1):
                print(f"      {j}. {win['factor']}")
                print(f"         Evidence: {win['evidence'][:80]}...")
                print(f"         Priority: {win['priority_score']:.1f}, Impact: {win['business_impact']}")
        
        # Sentiment breakdown
        sentiment = theme['sentiment_breakdown']
        print(f"   📊 Sentiment: {sentiment['positive']['count']} positive, {sentiment['negative']['count']} negative, {sentiment['neutral']['count']} neutral")
    
    # Comparison with old system
    print(f"\n🔄 COMPARISON WITH OLD SYSTEM:")
    print(f"   Old System: 1.0/10 (only negative themes)")
    print(f"   New System: {overall['overall_score']}/10 (Stage 2 integrated)")
    print(f"   Improvement: +{overall['overall_score'] - 1.0:.1f} points")
    
    if overall['overall_score'] > 5.0:
        print(f"   ✅ Result: Much more balanced assessment with clear improvement focus")
    elif overall['overall_score'] > 3.0:
        print(f"   ⚠️  Result: Mixed feedback with prioritized improvement opportunities")
    else:
        print(f"   ❌ Result: Significant challenges identified with clear action plan")
    
    return result

if __name__ == "__main__":
    test_stage2_integrated_themes() 