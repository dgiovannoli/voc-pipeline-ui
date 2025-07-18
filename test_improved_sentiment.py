#!/usr/bin/env python3
"""
Test script for improved sentiment handling with 0-5 relevance and categorical sentiments
"""

import os
import json
from enhanced_stage2_analyzer import SupabaseStage2Analyzer
from supabase_database import SupabaseDatabase

def test_improved_sentiment():
    """Test the improved sentiment handling with relevance scores and categorical sentiments"""
    try:
        print("🧪 Testing improved sentiment handling...")
        
        # Create analyzer with small batch for testing
        analyzer = SupabaseStage2Analyzer(batch_size=5, max_workers=1)
        
        # Test the sentiment calculation logic
        print("\n📊 Testing sentiment calculation logic...")
        
        # Test case 1: Single criterion with positive sentiment
        relevance_scores = {'product_capability': 4}
        criterion_sentiments = {'product_capability': 'positive'}
        overall = analyzer._calculate_overall_sentiment(relevance_scores, criterion_sentiments)
        print(f"Single positive criterion: {overall} (expected: positive)")
        
        # Test case 2: Multiple criteria with different sentiments
        relevance_scores = {
            'product_capability': 4,  # High relevance, positive
            'support_service_quality': 2  # Lower relevance, negative
        }
        criterion_sentiments = {
            'product_capability': 'positive',
            'support_service_quality': 'negative'
        }
        overall = analyzer._calculate_overall_sentiment(relevance_scores, criterion_sentiments)
        print(f"Mixed sentiments (positive dominant): {overall} (expected: positive)")
        
        # Test case 3: Conflicting sentiments with equal weights
        relevance_scores = {
            'product_capability': 3,
            'support_service_quality': 3
        }
        criterion_sentiments = {
            'product_capability': 'positive',
            'support_service_quality': 'negative'
        }
        overall = analyzer._calculate_overall_sentiment(relevance_scores, criterion_sentiments)
        print(f"Conflicting equal weights: {overall} (expected: mixed)")
        
        # Test case 4: Multiple criteria with neutral
        relevance_scores = {
            'product_capability': 2,
            'implementation_onboarding': 1
        }
        criterion_sentiments = {
            'product_capability': 'neutral',
            'implementation_onboarding': 'neutral'
        }
        overall = analyzer._calculate_overall_sentiment(relevance_scores, criterion_sentiments)
        print(f"All neutral: {overall} (expected: neutral)")
        
        # Test case 5: High relevance negative sentiment
        relevance_scores = {'security_compliance': 5}
        criterion_sentiments = {'security_compliance': 'negative'}
        overall = analyzer._calculate_overall_sentiment(relevance_scores, criterion_sentiments)
        print(f"High relevance negative: {overall} (expected: negative)")
        
        print("\n✅ Sentiment calculation tests completed!")
        
        # Test with a small batch of real data
        print("\n🔄 Testing with real data (first 5 quotes)...")
        
        # Clear existing Stage 2 data for clean test
        db = SupabaseDatabase()
        result = db.supabase.table('stage2_response_labeling').delete().eq('client_id', 'Rev').execute()
        print(f"Cleared {len(result.data)} existing Stage 2 records")
        
        # Run analysis on first 5 quotes
        result = analyzer.process_incremental(client_id="Rev")
        
        if result and result.get('success'):
            print(f"✅ Stage 2 analysis completed!")
            print(f"📊 Processed quotes: {result.get('processed_quotes', 0)}")
            print(f"📊 Analyzed quotes: {result.get('analyzed_quotes', 0)}")
            
            # Check the results
            df = db.get_stage2_response_labeling(client_id='Rev')
            print(f"\n📋 Stage 2 results:")
            print(f"Total records: {len(df)}")
            print(f"Unique quotes: {df['quote_id'].nunique()}")
            
            if len(df) > 0:
                print(f"\n📊 Sentiment distribution:")
                print(df['sentiment'].value_counts())
                
                print(f"\n📊 Relevance score distribution:")
                print(df['relevance_score'].value_counts().sort_index())
                
                print(f"\n📊 Criteria distribution:")
                print(df['criterion'].value_counts())
                
                # Show a sample result with enhanced explanation
                sample_record = df.iloc[0]
                if 'relevance_explanation' in sample_record:
                    try:
                        explanation = json.loads(sample_record['relevance_explanation'])
                        print(f"\n🔍 Sample analysis:")
                        print(f"Quote ID: {sample_record['quote_id']}")
                        print(f"Primary criterion: {explanation.get('primary_criterion')}")
                        print(f"Secondary criterion: {explanation.get('secondary_criterion')}")
                        print(f"Tertiary criterion: {explanation.get('tertiary_criterion')}")
                        print(f"Relevance scores: {explanation.get('all_relevance_scores')}")
                        print(f"Criterion sentiments: {explanation.get('criterion_sentiments')}")
                        print(f"Overall sentiment: {explanation.get('overall_sentiment')}")
                        print(f"Primary sentiment: {sample_record['sentiment']}")
                        print(f"Primary relevance score: {sample_record['relevance_score']}")
                    except:
                        print("Could not parse enhanced explanation")
            
        else:
            print("❌ Stage 2 analysis failed")
            
    except Exception as e:
        print(f"❌ Error in sentiment handling test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_improved_sentiment() 