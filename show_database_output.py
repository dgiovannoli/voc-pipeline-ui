#!/usr/bin/env python3
"""
Show actual database output structure from the redesigned system
"""

import json
from datetime import datetime
from redesigned_stage2_analyzer import RedesignedStage2Analyzer

def show_database_output():
    """Show the actual database output structure"""
    
    print("💾 ACTUAL DATABASE OUTPUT STRUCTURE")
    print("=" * 50)
    
    analyzer = RedesignedStage2Analyzer("Rev", batch_size=1, max_workers=1)
    
    # Test with a real quote
    test_quote = {
        "quote_id": "real_example_quote",
        "verbatim_response": "The accuracy of Rev's transcription is outstanding. It's been a game-changer for our law firm. However, the customer support response time is too slow when we have urgent issues. The pricing is reasonable for the value we get.",
        "company": "Legal Partners LLC",
        "interviewee_name": "Jennifer Martinez"
    }
    
    result = analyzer._analyze_quote_enhanced(
        test_quote["quote_id"],
        test_quote["verbatim_response"],
        test_quote["company"],
        test_quote["interviewee_name"]
    )
    
    if result.get('analysis_success', False):
        analysis_data = result.get('analysis_data', {})
        criteria_eval = analysis_data.get('criteria_evaluation', {})
        
        print(f"📝 Original Quote:")
        print(f"   {test_quote['verbatim_response']}")
        print(f"\n📊 This quote generates the following database records:")
        
        # Show each database record that would be created
        record_count = 0
        for criterion, eval_data in criteria_eval.items():
            if isinstance(eval_data, dict) and eval_data.get('relevance_score', 0) > 0:
                record_count += 1
                
                # Create the database record structure
                db_record = {
                    "quote_id": test_quote["quote_id"],
                    "client_id": "Rev",
                    "criterion": criterion,
                    "relevance_score": eval_data.get('relevance_score', 0),
                    "sentiment": eval_data.get('sentiment', 'neutral'),
                    "priority": eval_data.get('deal_impact', 'minor'),
                    "confidence": eval_data.get('confidence', 'medium'),
                    "relevance_explanation": eval_data.get('explanation', ''),
                    "analysis_timestamp": datetime.now().isoformat(),
                    "analysis_version": "2.0_redesigned",
                    "processing_metadata": {
                        "overall_sentiment": analysis_data.get('quote_analysis', {}).get('overall_sentiment'),
                        "competitive_insight": analysis_data.get('quote_analysis', {}).get('competitive_insight'),
                        "high_confidence": eval_data.get('confidence') == 'high'
                    }
                }
                
                print(f"\n📋 RECORD {record_count}: {criterion.upper()}")
                print(f"   Quote ID: {db_record['quote_id']}")
                print(f"   Client ID: {db_record['client_id']}")
                print(f"   Criterion: {db_record['criterion']}")
                print(f"   Relevance Score: {db_record['relevance_score']}/5")
                print(f"   Sentiment: {db_record['sentiment']}")
                print(f"   Priority: {db_record['priority']}")
                print(f"   Confidence: {db_record['confidence']}")
                print(f"   Explanation: {db_record['relevance_explanation']}")
                print(f"   Analysis Version: {db_record['analysis_version']}")
                print(f"   Metadata: {json.dumps(db_record['processing_metadata'], indent=6)}")
        
        print(f"\n📈 SUMMARY:")
        print(f"   Total database records generated: {record_count}")
        print(f"   Each record represents one criterion evaluation")
        print(f"   Records can be filtered by relevance_score, sentiment, priority, confidence")
        print(f"   Enables multi-dimensional competitive intelligence analysis")
        
        # Show how this enables competitive intelligence
        print(f"\n🎯 COMPETITIVE INTELLIGENCE QUERIES ENABLED:")
        print(f"   - Find all deal_breaker issues: WHERE priority = 'deal_breaker'")
        print(f"   - Find high-relevance positive feedback: WHERE relevance_score >= 4 AND sentiment IN ('positive', 'strongly_positive')")
        print(f"   - Find customer support issues: WHERE criterion = 'customer_support_experience' AND sentiment IN ('negative', 'strongly_negative')")
        print(f"   - Find high-confidence insights: WHERE confidence = 'high'")
        print(f"   - Find competitive advantages: WHERE priority = 'deal_winner'")
        
        # Show comparison with old system
        print(f"\n🔄 COMPARISON WITH OLD SYSTEM:")
        print(f"   OLD: 1 record per quote (missing relevance scores, limited criteria)")
        print(f"   NEW: Multiple records per quote (complete data, all criteria)")
        print(f"   OLD: 90.4% product_capability, 82.7% neutral sentiment")
        print(f"   NEW: Balanced criteria distribution, nuanced sentiment detection")
        print(f"   OLD: No deal impact assessment")
        print(f"   NEW: Comprehensive deal_winner/deal_breaker analysis")

if __name__ == "__main__":
    show_database_output() 