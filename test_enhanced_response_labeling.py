#!/usr/bin/env python3
"""
Test script for enhanced response labeling system
Tests the three priority improvements:
1. Fixed LLM parsing
2. Enhanced sentiment analysis  
3. Multi-criteria capture
"""

import os
import json
import pandas as pd
from enhanced_stage2_analyzer import SupabaseStage2Analyzer
from supabase_database import SupabaseDatabase

def test_enhanced_response_labeling():
    """Test the enhanced response labeling system"""
    print("🧪 Testing Enhanced Response Labeling System")
    print("=" * 60)
    
    # Initialize analyzer with smaller batch for testing
    analyzer = SupabaseStage2Analyzer(batch_size=5, max_workers=1)
    
    # Test 1: LLM Parsing
    print("\n1️⃣ Testing Enhanced LLM Parsing...")
    test_llm_parsing(analyzer)
    
    # Test 2: Sentiment Analysis
    print("\n2️⃣ Testing Enhanced Sentiment Analysis...")
    test_sentiment_analysis(analyzer)
    
    # Test 3: Multi-Criteria Capture
    print("\n3️⃣ Testing Multi-Criteria Capture...")
    test_multi_criteria_capture(analyzer)
    
    # Test 4: End-to-End Processing
    print("\n4️⃣ Testing End-to-End Processing...")
    test_end_to_end_processing(analyzer)

def test_llm_parsing(analyzer):
    """Test the enhanced LLM parsing capabilities"""
    print("   Testing JSON response parsing...")
    
    # Test with a sample quote
    test_quote = {
        'response_id': 'test_quote_1',
        'verbatim_response': 'I love the accuracy of the transcription service. It saves me hours every week and the support team is always helpful when I have questions.',
        'subject': 'Transcription Accuracy',
        'company': 'Test Law Firm',
        'interviewee_name': 'Test Attorney'
    }
    
    # Convert to DataFrame
    test_df = pd.DataFrame([test_quote])
    
    # Prepare batch text
    batch_text = analyzer._prepare_batch_for_llm(test_df)
    
    try:
        # Call LLM
        llm_response = analyzer._call_llm_batch(batch_text)
        print(f"   ✅ LLM Response received: {len(llm_response)} characters")
        
        # Test parsing
        parsed_results = analyzer._parse_llm_batch_response(llm_response, test_df)
        
        if parsed_results and len(parsed_results) > 0:
            result = parsed_results[0]
            print(f"   ✅ Parsing successful: {result.get('quote_id')}")
            print(f"   ✅ Primary criterion: {result.get('primary_criterion')}")
            print(f"   ✅ Overall sentiment: {result.get('overall_sentiment')}")
            return True
        else:
            print("   ❌ Parsing failed - no results")
            return False
            
    except Exception as e:
        print(f"   ❌ LLM parsing test failed: {e}")
        return False

def test_sentiment_analysis(analyzer):
    """Test the enhanced sentiment analysis"""
    print("   Testing sentiment analysis with different quote types...")
    
    test_quotes = [
        {
            'response_id': 'positive_quote',
            'verbatim_response': 'The transcription accuracy is excellent and it has completely transformed our workflow. Highly recommend!',
            'subject': 'Positive Feedback',
            'company': 'Test Company',
            'interviewee_name': 'Test User'
        },
        {
            'response_id': 'negative_quote', 
            'verbatim_response': 'The service is terrible. Constant errors and the support team never responds. Waste of money.',
            'subject': 'Negative Feedback',
            'company': 'Test Company',
            'interviewee_name': 'Test User'
        },
        {
            'response_id': 'mixed_quote',
            'verbatim_response': 'The accuracy is good but the pricing is too expensive. Support is helpful though.',
            'subject': 'Mixed Feedback', 
            'company': 'Test Company',
            'interviewee_name': 'Test User'
        }
    ]
    
    # Convert to DataFrame
    test_df = pd.DataFrame(test_quotes)
    batch_text = analyzer._prepare_batch_for_llm(test_df)
    
    try:
        llm_response = analyzer._call_llm_batch(batch_text)
        parsed_results = analyzer._parse_llm_batch_response(llm_response, test_df)
        
        sentiment_results = {}
        for result in parsed_results:
            quote_id = result.get('quote_id')
            sentiment = result.get('overall_sentiment')
            criterion_sentiments = result.get('criterion_sentiments', {})
            sentiment_results[quote_id] = {
                'overall': sentiment,
                'criterion_sentiments': criterion_sentiments
            }
        
        print(f"   ✅ Sentiment analysis results:")
        for quote_id, sentiments in sentiment_results.items():
            print(f"      {quote_id}: {sentiments['overall']} (criterion sentiments: {sentiments['criterion_sentiments']})")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Sentiment analysis test failed: {e}")
        return False

def test_multi_criteria_capture(analyzer):
    """Test the multi-criteria capture functionality"""
    print("   Testing multi-criteria capture...")
    
    test_quote = {
        'response_id': 'multi_criteria_quote',
        'verbatim_response': 'The product capabilities are great and the implementation was smooth. However, the pricing is too high and support response times are slow. The integration with our existing systems works well though.',
        'subject': 'Multi-Criteria Feedback',
        'company': 'Test Company', 
        'interviewee_name': 'Test User'
    }
    
    # Convert to DataFrame
    test_df = pd.DataFrame([test_quote])
    batch_text = analyzer._prepare_batch_for_llm(test_df)
    
    try:
        llm_response = analyzer._call_llm_batch(batch_text)
        parsed_results = analyzer._parse_llm_batch_response(llm_response, test_df)
        
        if parsed_results:
            result = parsed_results[0]
            relevance_scores = result.get('relevance_scores', {})
            criterion_sentiments = result.get('criterion_sentiments', {})
            
            print(f"   ✅ Multi-criteria capture successful:")
            print(f"      Primary criterion: {result.get('primary_criterion')}")
            print(f"      Secondary criterion: {result.get('secondary_criterion')}")
            print(f"      Tertiary criterion: {result.get('tertiary_criterion')}")
            
            # Show criteria with scores > 0
            active_criteria = [(criterion, score) for criterion, score in relevance_scores.items() if score > 0]
            print(f"      Active criteria: {len(active_criteria)}")
            for criterion, score in active_criteria:
                sentiment = criterion_sentiments.get(criterion, 'neutral')
                print(f"        {criterion}: {score}/5 ({sentiment})")
            
            return True
        else:
            print("   ❌ Multi-criteria capture failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Multi-criteria test failed: {e}")
        return False

def test_end_to_end_processing(analyzer):
    """Test end-to-end processing with a small batch"""
    print("   Testing end-to-end processing...")
    
    try:
        # Get a small sample of quotes from database
        db = SupabaseDatabase()
        quotes_df = db.get_stage1_data_responses(client_id='Rev')
        
        if quotes_df.empty:
            print("   ⚠️ No quotes found in database for testing")
            return False
        
        # Take first 3 quotes for testing
        test_quotes = quotes_df.head(3)
        print(f"   Testing with {len(test_quotes)} quotes from database")
        
        # Process the batch
        batch_text = analyzer._prepare_batch_for_llm(test_quotes)
        llm_response = analyzer._call_llm_batch(batch_text)
        parsed_results = analyzer._parse_llm_batch_response(llm_response, test_quotes)
        
        if parsed_results:
            print(f"   ✅ End-to-end processing successful: {len(parsed_results)} results")
            
            # Show sample results
            for i, result in enumerate(parsed_results[:2]):
                print(f"      Result {i+1}:")
                print(f"        Quote ID: {result.get('quote_id')}")
                print(f"        Primary: {result.get('primary_criterion')} ({result.get('relevance_scores', {}).get(result.get('primary_criterion'), 0)}/5)")
                print(f"        Sentiment: {result.get('overall_sentiment')}")
                print(f"        Confidence: {result.get('confidence')}")
            
            return True
        else:
            print("   ❌ End-to-end processing failed")
            return False
            
    except Exception as e:
        print(f"   ❌ End-to-end test failed: {e}")
        return False

def run_enhanced_analysis():
    """Run the enhanced analysis on actual data"""
    print("\n🚀 Running Enhanced Response Labeling Analysis")
    print("=" * 60)
    
    try:
        analyzer = SupabaseStage2Analyzer(batch_size=10, max_workers=1)
        
        # Run analysis on Rev client
        result = analyzer.process_incremental(client_id="Rev")
        
        if result and result.get('success'):
            print(f"✅ Enhanced analysis completed!")
            print(f"📊 Processed quotes: {result.get('processed_quotes', 0)}")
            print(f"📊 Analyzed quotes: {result.get('analyzed_quotes', 0)}")
            print(f"📈 Success rate: {result.get('success_rate', 0)*100:.1f}%")
            
            # Check the results
            db = SupabaseDatabase()
            stage2_df = db.get_stage2_response_labeling(client_id="Rev")
            
            print(f"\n📊 Enhanced Results Summary:")
            print(f"Total Stage 2 records: {len(stage2_df)}")
            
            if not stage2_df.empty:
                # Check for enhanced features
                print(f"Records with sentiment: {stage2_df['sentiment'].notna().sum()}")
                print(f"Records with relevance scores: {stage2_df['relevance_score'].notna().sum()}")
                
                # Show sample enhanced record
                sample_record = stage2_df.iloc[0]
                print(f"\n📋 Sample Enhanced Record:")
                print(f"Quote ID: {sample_record['quote_id']}")
                print(f"Criterion: {sample_record['criterion']}")
                print(f"Relevance Score: {sample_record['relevance_score']}")
                print(f"Sentiment: {sample_record['sentiment']}")
                print(f"Priority: {sample_record['priority']}")
                print(f"Confidence: {sample_record['confidence']}")
                
                # Parse enhanced explanation
                try:
                    explanation = json.loads(sample_record['relevance_explanation'])
                    print(f"Enhanced Explanation Keys: {list(explanation.keys())}")
                    if 'all_relevance_scores' in explanation:
                        print(f"All Relevance Scores: {explanation['all_relevance_scores']}")
                except:
                    print("Could not parse enhanced explanation")
            
            return True
        else:
            print("❌ Enhanced analysis failed")
            return False
            
    except Exception as e:
        print(f"❌ Enhanced analysis error: {e}")
        return False

if __name__ == "__main__":
    # Run tests
    test_enhanced_response_labeling()
    
    # Run actual analysis
    run_enhanced_analysis() 