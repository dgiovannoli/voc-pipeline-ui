"""
Test script for Holistic Evaluation System
Demonstrates how the new system provides balanced sentiment analysis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from official_scripts.holistic_evaluation import HolisticEvaluator
from official_scripts.database.supabase_database import SupabaseDatabase

def test_holistic_evaluation():
    """
    Test the holistic evaluation system
    """
    print("🎯 TESTING HOLISTIC EVALUATION SYSTEM")
    print("=" * 60)
    
    # Initialize components
    evaluator = HolisticEvaluator()
    db = SupabaseDatabase()
    
    # Get all quotes for Rev
    quotes = db.get_stage1_data_responses(client_id='Rev')
    print(f"📊 Retrieved {len(quotes)} quotes for Rev analysis")
    
    # Test Product Capabilities evaluation
    print("\n🔍 TESTING PRODUCT CAPABILITIES & FEATURES EVALUATION")
    print("-" * 50)
    
    # Create mock criterion data
    criterion_data = {
        'framework': {
            'title': 'Product Capability & Features',
            'business_impact': 'Directly impacts customer retention and satisfaction',
            'executive_description': 'Core product functionality that drives user satisfaction'
        }
    }
    
    # Run holistic evaluation
    result = evaluator.evaluate_criterion_holistically(criterion_data, quotes)
    
    # Display results
    print(f"📈 HOLISTIC SCORE: {result['holistic_score']}/10")
    print(f"🎯 PERFORMANCE LEVEL: {result['performance_assessment']['level']}")
    print(f"📝 DESCRIPTION: {result['performance_assessment']['description']}")
    
    # Sentiment breakdown
    sentiment = result['sentiment_breakdown']
    print(f"\n📊 SENTIMENT BREAKDOWN:")
    print(f"   Positive quotes: {sentiment['positive']['count']} (score: {sentiment['positive']['weighted_score']:.2f})")
    print(f"   Negative quotes: {sentiment['negative']['count']} (score: {sentiment['negative']['weighted_score']:.2f})")
    print(f"   Neutral quotes: {sentiment['neutral']['count']} (score: {sentiment['neutral']['weighted_score']:.2f})")
    
    # Improvement opportunities and winning factors
    improvement_opps = result['improvement_opportunities']
    winning_factors = result['winning_factors']
    
    print(f"\n📈 IMPROVEMENT OPPORTUNITIES (Priority 1) ({len(improvement_opps['improvement_opportunities'])}):")
    for i, opportunity in enumerate(improvement_opps['improvement_opportunities'], 1):
        print(f"   {i}. {opportunity['opportunity']}")
        print(f"      Evidence: {opportunity['evidence'][:100]}...")
        print(f"      Source: {opportunity['interviewee']} at {opportunity['company']}")
        print()
    
    print(f"🏆 WINNING FACTORS (Priority 2) ({len(winning_factors['winning_factors'])}):")
    for i, factor in enumerate(winning_factors['winning_factors'], 1):
        print(f"   {i}. {factor['factor']}")
        print(f"      Evidence: {factor['evidence'][:100]}...")
        print(f"      Source: {factor['interviewee']} at {factor['company']}")
        print()
    
    # Evidence summary
    evidence = result['evidence_summary']
    print(f"\n📋 EVIDENCE SUMMARY:")
    print(f"   Total quotes analyzed: {evidence['total_quotes']}")
    print(f"   Unique companies: {evidence['unique_companies']}")
    print(f"   High-priority quotes: {evidence['priority_quotes']}")
    
    # Sample positive quotes
    print(f"\n💬 SAMPLE POSITIVE QUOTES:")
    for i, quote in enumerate(sentiment['positive']['quotes'][:3], 1):
        print(f"   {i}. \"{quote['verbatim_response'][:150]}...\"")
        print(f"      - {quote.get('interviewee_name', 'Unknown')} at {quote.get('company', 'Unknown')}")
        print(f"      - Sentiment Score: {quote['sentiment']['score']:.2f}")
        print()
    
    # Sample negative quotes
    print(f"💬 SAMPLE NEGATIVE QUOTES:")
    for i, quote in enumerate(sentiment['negative']['quotes'][:3], 1):
        print(f"   {i}. \"{quote['verbatim_response'][:150]}...\"")
        print(f"      - {quote.get('interviewee_name', 'Unknown')} at {quote.get('company', 'Unknown')}")
        print(f"      - Sentiment Score: {quote['sentiment']['score']:.2f}")
        print()
    
    # Comparison with old system
    print(f"\n🔄 COMPARISON WITH OLD SYSTEM:")
    print(f"   Old System Score: 1.0/10 (only negative themes)")
    print(f"   New Holistic Score: {result['holistic_score']}/10 (balanced sentiment)")
    print(f"   Improvement: +{result['holistic_score'] - 1.0:.1f} points")
    
    if result['holistic_score'] > 5.0:
        print(f"   ✅ Result: Much more balanced assessment for paying customers")
    elif result['holistic_score'] > 3.0:
        print(f"   ⚠️  Result: Mixed feedback with clear improvement opportunities")
    else:
        print(f"   ❌ Result: Significant challenges identified")
    
    return result

if __name__ == "__main__":
    test_holistic_evaluation() 