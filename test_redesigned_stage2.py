#!/usr/bin/env python3
"""
Test script for redesigned Stage 2 analyzer
"""

import json
from redesigned_stage2_analyzer import RedesignedStage2Analyzer

def test_redesigned_analyzer():
    """Test the redesigned Stage 2 analyzer with sample quotes"""
    
    print("🧪 Testing Redesigned Stage 2 Analyzer")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = RedesignedStage2Analyzer("Rev", batch_size=5, max_workers=1)
    
    # Test quotes with different characteristics
    test_quotes = [
        {
            "quote_id": "test_positive_product",
            "verbatim_response": "I love the accuracy of the transcription service. It's been a game-changer for our law firm. The accuracy is outstanding and it saves us hours every week.",
            "company": "Test Law Firm",
            "interviewee_name": "Test Attorney"
        },
        {
            "quote_id": "test_negative_support",
            "verbatim_response": "The customer support is terrible. When we had an issue, it took days to get a response. This is a deal breaker for us.",
            "company": "Test Company",
            "interviewee_name": "Test Manager"
        },
        {
            "quote_id": "test_neutral_implementation",
            "verbatim_response": "The implementation was okay. It took about a week to get everything set up. The training was adequate.",
            "company": "Test Corp",
            "interviewee_name": "Test Director"
        },
        {
            "quote_id": "test_mixed_commercial",
            "verbatim_response": "The price is reasonable for what we get, but the contract terms are too rigid. We need more flexibility.",
            "company": "Test Inc",
            "interviewee_name": "Test VP"
        },
        {
            "quote_id": "test_competitive",
            "verbatim_response": "We compared Rev to Otter and TurboScribe. Rev's accuracy is better, but Otter is faster. Speed matters for our workflow.",
            "company": "Test LLC",
            "interviewee_name": "Test Executive"
        }
    ]
    
    print(f"📝 Testing with {len(test_quotes)} sample quotes")
    
    # Test individual quote analysis
    for i, quote in enumerate(test_quotes, 1):
        print(f"\n🔍 Testing Quote {i}: {quote['quote_id']}")
        print(f"Text: {quote['verbatim_response'][:100]}...")
        
        try:
            # Analyze quote
            result = analyzer._analyze_quote_enhanced(
                quote['quote_id'],
                quote['verbatim_response'],
                quote['company'],
                quote['interviewee_name']
            )
            
            if result.get('analysis_success', False):
                analysis_data = result.get('analysis_data', {})
                quote_analysis = analysis_data.get('quote_analysis', {})
                criteria_eval = analysis_data.get('criteria_evaluation', {})
                overall_metrics = analysis_data.get('overall_metrics', {})
                
                print(f"✅ Analysis successful")
                print(f"   Overall sentiment: {quote_analysis.get('overall_sentiment')}")
                print(f"   Primary criterion: {quote_analysis.get('primary_criterion')}")
                print(f"   Deal impact: {quote_analysis.get('deal_impact')}")
                print(f"   Criteria evaluated: {overall_metrics.get('total_criteria_evaluated')}")
                print(f"   Average relevance: {overall_metrics.get('average_relevance_score')}")
                
                # Show top criteria
                top_criteria = sorted(
                    criteria_eval.items(),
                    key=lambda x: x[1].get('relevance_score', 0),
                    reverse=True
                )[:3]
                
                print(f"   Top criteria:")
                for criterion, eval_data in top_criteria:
                    if isinstance(eval_data, dict):
                        print(f"     - {criterion}: {eval_data.get('relevance_score')}/5 ({eval_data.get('sentiment')})")
                
            else:
                print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error during analysis: {str(e)}")
    
    print(f"\n🎯 Testing Complete")
    print("=" * 50)

if __name__ == "__main__":
    test_redesigned_analyzer() 