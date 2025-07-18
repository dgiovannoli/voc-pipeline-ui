#!/usr/bin/env python3
"""
Quick test for improved Stage 2 analyzer with optimized parallel processing
"""

import os
import time
from enhanced_stage2_analyzer import SupabaseStage2Analyzer
from supabase_database import SupabaseDatabase

def test_optimized_stage2():
    """Test the improved Stage 2 analyzer with optimized settings"""
    try:
        print("🧪 Testing optimized Stage 2 analyzer...")
        
        # Create analyzer with optimized settings
        analyzer = SupabaseStage2Analyzer(batch_size=25, max_workers=4)  # Increased batch size and workers
        
        # Run analysis on first 50 quotes only for testing
        print("Running Stage 2 analysis on first 50 quotes...")
        start_time = time.time()
        
        result = analyzer.process_incremental(client_id="Rev")
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result and result.get('success'):
            print(f"✅ Stage 2 analysis completed in {duration:.1f} seconds!")
            print(f"📊 Processed quotes: {result.get('processed_quotes', 0)}")
            print(f"📊 Analyzed quotes: {result.get('analyzed_quotes', 0)}")
            print(f"📈 Success rate: {result.get('success_rate', 0)*100:.1f}%")
            print(f"⚡ Speed: {result.get('analyzed_quotes', 0)/duration:.1f} quotes/second")
            
            # Check the results
            db = SupabaseDatabase()
            stage2_df = db.get_stage2_response_labeling(client_id="Rev")
            
            print(f"\n📊 Results:")
            print(f"Total Stage 2 records: {len(stage2_df)}")
            if len(stage2_df) > 0:
                print(f"Unique quotes: {stage2_df['quote_id'].nunique()}")
                print(f"Records per quote: {len(stage2_df)/stage2_df['quote_id'].nunique():.1f}")
                
                # Show sample results
                print(f"\n📋 Sample results:")
                for i, row in stage2_df.head(2).iterrows():
                    print(f"Quote: {row['quote_id']}")
                    print(f"Primary criterion: {row['criterion']}")
                    print(f"Score: {row['relevance_score']}")
                    print(f"Sentiment: {row['sentiment']}")
                    print("---")
                
                # Verify we have 1 record per quote
                if len(stage2_df) == stage2_df['quote_id'].nunique():
                    print("✅ SUCCESS: 1 record per quote achieved!")
                else:
                    print("❌ ISSUE: Multiple records per quote detected")
            else:
                print("No records found - analysis may have failed")
                
        else:
            print(f"❌ Stage 2 analysis failed: {result}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_optimized_stage2() 