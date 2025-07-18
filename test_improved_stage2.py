#!/usr/bin/env python3
"""
Test script for improved Stage 2 analyzer
"""

import os
from enhanced_stage2_analyzer import SupabaseStage2Analyzer
from supabase_database import SupabaseDatabase

def test_improved_stage2():
    """Test the improved Stage 2 analyzer"""
    try:
        print("🧪 Testing improved Stage 2 analyzer...")
        
        # Create analyzer
        analyzer = SupabaseStage2Analyzer(batch_size=10, max_workers=1)  # Small batch for testing
        
        # Run analysis on a small subset
        print("Running Stage 2 analysis...")
        result = analyzer.process_incremental(client_id="Rev")
        
        if result and result.get('success'):
            print(f"✅ Stage 2 analysis completed!")
            print(f"📊 Processed quotes: {result.get('processed_quotes', 0)}")
            print(f"📊 Analyzed quotes: {result.get('analyzed_quotes', 0)}")
            print(f"📈 Success rate: {result.get('success_rate', 0)*100:.1f}%")
            
            # Check the results
            db = SupabaseDatabase()
            stage2_df = db.get_stage2_response_labeling(client_id="Rev")
            
            print(f"\n📊 Results:")
            print(f"Total Stage 2 records: {len(stage2_df)}")
            print(f"Unique quotes: {stage2_df['quote_id'].nunique()}")
            print(f"Records per quote: {len(stage2_df)/stage2_df['quote_id'].nunique():.1f}")
            
            # Show sample results
            print(f"\n📋 Sample results:")
            for i, row in stage2_df.head(3).iterrows():
                print(f"Quote: {row['quote_id']}")
                print(f"Primary criterion: {row['criterion']}")
                print(f"Score: {row['relevance_score']}")
                print(f"Sentiment: {row['sentiment']}")
                print(f"Explanation: {row['relevance_explanation'][:100]}...")
                print("---")
            
            # Verify we have 1 record per quote
            if len(stage2_df) == stage2_df['quote_id'].nunique():
                print("✅ SUCCESS: 1 record per quote achieved!")
            else:
                print("❌ ISSUE: Multiple records per quote detected")
                
        else:
            print(f"❌ Stage 2 analysis failed: {result}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_improved_stage2() 