#!/usr/bin/env python3
"""
Show detailed output examples from the redesigned Stage 2 system
"""

import json
from redesigned_stage2_analyzer import RedesignedStage2Analyzer

def show_detailed_output_examples():
    """Show detailed output examples from the redesigned system"""
    
    print("📋 DETAILED OUTPUT EXAMPLES - REDESIGNED STAGE 2 SYSTEM")
    print("=" * 70)
    
    analyzer = RedesignedStage2Analyzer("Rev", batch_size=1, max_workers=1)
    
    # Example 1: Positive product feedback
    print("\n🎯 EXAMPLE 1: POSITIVE PRODUCT FEEDBACK")
    print("-" * 50)
    
    quote1 = {
        "quote_id": "example_positive_product",
        "verbatim_response": "I love the accuracy of the transcription service. It's been a game-changer for our law firm. The accuracy is outstanding and it saves us hours every week. We've tried other services but Rev is by far the most accurate.",
        "company": "Smith & Associates Law",
        "interviewee_name": "Sarah Johnson"
    }
    
    result1 = analyzer._analyze_quote_enhanced(
        quote1["quote_id"],
        quote1["verbatim_response"],
        quote1["company"],
        quote1["interviewee_name"]
    )
    
    if result1.get('analysis_success', False):
        analysis_data = result1.get('analysis_data', {})
        
        print(f"📝 Quote: {quote1['verbatim_response']}")
        print(f"\n📊 ANALYSIS RESULTS:")
        
        # Quote analysis
        quote_analysis = analysis_data.get('quote_analysis', {})
        print(f"   Overall Sentiment: {quote_analysis.get('overall_sentiment')}")
        print(f"   Primary Criterion: {quote_analysis.get('primary_criterion')}")
        print(f"   Deal Impact: {quote_analysis.get('deal_impact')}")
        print(f"   Competitive Insight: {quote_analysis.get('competitive_insight')}")
        
        # Criteria evaluation
        criteria_eval = analysis_data.get('criteria_evaluation', {})
        print(f"\n📋 CRITERIA EVALUATION:")
        for criterion, eval_data in criteria_eval.items():
            if isinstance(eval_data, dict) and eval_data.get('relevance_score', 0) > 0:
                print(f"   {criterion}:")
                print(f"     - Relevance Score: {eval_data.get('relevance_score')}/5")
                print(f"     - Sentiment: {eval_data.get('sentiment')}")
                print(f"     - Deal Impact: {eval_data.get('deal_impact')}")
                print(f"     - Confidence: {eval_data.get('confidence')}")
                print(f"     - Explanation: {eval_data.get('explanation')}")
        
        # Competitive insights
        competitive_insights = analysis_data.get('competitive_insights', {})
        print(f"\n🎯 COMPETITIVE INSIGHTS:")
        for insight_type, insights in competitive_insights.items():
            if insights:
                print(f"   {insight_type.title()}:")
                for insight in insights:
                    print(f"     - {insight}")
        
        # Overall metrics
        overall_metrics = analysis_data.get('overall_metrics', {})
        print(f"\n📈 OVERALL METRICS:")
        print(f"   Criteria Evaluated: {overall_metrics.get('total_criteria_evaluated')}")
        print(f"   Criteria with Relevance: {overall_metrics.get('criteria_with_relevance')}")
        print(f"   Average Relevance Score: {overall_metrics.get('average_relevance_score')}")
        print(f"   Primary Criterion: {overall_metrics.get('primary_criterion')}")
        print(f"   Primary Relevance Score: {overall_metrics.get('primary_relevance_score')}")
    
    # Example 2: Negative support feedback
    print(f"\n\n🎯 EXAMPLE 2: NEGATIVE SUPPORT FEEDBACK")
    print("-" * 50)
    
    quote2 = {
        "quote_id": "example_negative_support",
        "verbatim_response": "The customer support is terrible. When we had an issue, it took days to get a response. This is a deal breaker for us. We need reliable support for our business-critical operations.",
        "company": "Tech Solutions Inc",
        "interviewee_name": "Mike Chen"
    }
    
    result2 = analyzer._analyze_quote_enhanced(
        quote2["quote_id"],
        quote2["verbatim_response"],
        quote2["company"],
        quote2["interviewee_name"]
    )
    
    if result2.get('analysis_success', False):
        analysis_data = result2.get('analysis_data', {})
        
        print(f"📝 Quote: {quote2['verbatim_response']}")
        print(f"\n📊 ANALYSIS RESULTS:")
        
        # Quote analysis
        quote_analysis = analysis_data.get('quote_analysis', {})
        print(f"   Overall Sentiment: {quote_analysis.get('overall_sentiment')}")
        print(f"   Primary Criterion: {quote_analysis.get('primary_criterion')}")
        print(f"   Deal Impact: {quote_analysis.get('deal_impact')}")
        print(f"   Competitive Insight: {quote_analysis.get('competitive_insight')}")
        
        # Criteria evaluation
        criteria_eval = analysis_data.get('criteria_evaluation', {})
        print(f"\n📋 CRITERIA EVALUATION:")
        for criterion, eval_data in criteria_eval.items():
            if isinstance(eval_data, dict) and eval_data.get('relevance_score', 0) > 0:
                print(f"   {criterion}:")
                print(f"     - Relevance Score: {eval_data.get('relevance_score')}/5")
                print(f"     - Sentiment: {eval_data.get('sentiment')}")
                print(f"     - Deal Impact: {eval_data.get('deal_impact')}")
                print(f"     - Confidence: {eval_data.get('confidence')}")
                print(f"     - Explanation: {eval_data.get('explanation')}")
    
    # Example 3: Mixed commercial feedback
    print(f"\n\n🎯 EXAMPLE 3: MIXED COMMERCIAL FEEDBACK")
    print("-" * 50)
    
    quote3 = {
        "quote_id": "example_mixed_commercial",
        "verbatim_response": "The price is reasonable for what we get, but the contract terms are too rigid. We need more flexibility. The ROI is good, but the payment terms don't work for our cash flow.",
        "company": "Global Enterprises",
        "interviewee_name": "Lisa Rodriguez"
    }
    
    result3 = analyzer._analyze_quote_enhanced(
        quote3["quote_id"],
        quote3["verbatim_response"],
        quote3["company"],
        quote3["interviewee_name"]
    )
    
    if result3.get('analysis_success', False):
        analysis_data = result3.get('analysis_data', {})
        
        print(f"📝 Quote: {quote3['verbatim_response']}")
        print(f"\n📊 ANALYSIS RESULTS:")
        
        # Quote analysis
        quote_analysis = analysis_data.get('quote_analysis', {})
        print(f"   Overall Sentiment: {quote_analysis.get('overall_sentiment')}")
        print(f"   Primary Criterion: {quote_analysis.get('primary_criterion')}")
        print(f"   Deal Impact: {quote_analysis.get('deal_impact')}")
        print(f"   Competitive Insight: {quote_analysis.get('competitive_insight')}")
        
        # Criteria evaluation
        criteria_eval = analysis_data.get('criteria_evaluation', {})
        print(f"\n📋 CRITERIA EVALUATION:")
        for criterion, eval_data in criteria_eval.items():
            if isinstance(eval_data, dict) and eval_data.get('relevance_score', 0) > 0:
                print(f"   {criterion}:")
                print(f"     - Relevance Score: {eval_data.get('relevance_score')}/5")
                print(f"     - Sentiment: {eval_data.get('sentiment')}")
                print(f"     - Deal Impact: {eval_data.get('deal_impact')}")
                print(f"     - Confidence: {eval_data.get('confidence')}")
                print(f"     - Explanation: {eval_data.get('explanation')}")
    
    # Show database record structure
    print(f"\n\n💾 DATABASE RECORD STRUCTURE")
    print("-" * 50)
    print("Each quote generates multiple database records (one per relevant criterion):")
    print("""
    {
        "quote_id": "example_positive_product",
        "client_id": "Rev",
        "criterion": "product_capability",
        "relevance_score": 5,
        "sentiment": "strongly_positive",
        "priority": "deal_winner",
        "confidence": "high",
        "relevance_explanation": "Quote directly mentions accuracy and performance",
        "analysis_timestamp": "2024-01-15T10:30:00",
        "analysis_version": "2.0_redesigned",
        "processing_metadata": {
            "overall_sentiment": "positive",
            "competitive_insight": "Strong product differentiation on accuracy",
            "high_confidence": true
        }
    }
    """)
    
    # Show competitive intelligence value
    print(f"\n🎯 COMPETITIVE INTELLIGENCE VALUE")
    print("-" * 50)
    print("This output enables:")
    print("✅ Win/loss analysis with deal_winner/deal_breaker identification")
    print("✅ Competitive positioning with SWOT analysis")
    print("✅ Prioritization using relevance scores (0-5)")
    print("✅ Sentiment tracking across all criteria")
    print("✅ Confidence-based filtering for decision making")
    print("✅ Multi-criteria performance assessment")
    print("✅ Executive-ready competitive insights")

if __name__ == "__main__":
    show_detailed_output_examples() 