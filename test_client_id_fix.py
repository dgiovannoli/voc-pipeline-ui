#!/usr/bin/env python3
"""
Test script to verify that the client_id fix works correctly
"""

from supabase_database import SupabaseDatabase
from enhanced_stage2_analyzer import SupabaseStage2Analyzer

def test_client_id_fix():
    """Test that Stage 2 analysis uses the correct client_id"""
    
    print("🧪 Testing client_id fix in Stage 2 analyzer")
    print("=" * 50)
    
    try:
        # Initialize database
        db = SupabaseDatabase()
        
        # Check current data for both clients
        print("\n📊 Current data status:")
        
        # Check Rev client data
        rev_core = db.get_stage1_data_responses(client_id='Rev')
        rev_analysis = db.get_stage2_response_labeling(client_id='Rev')
        print(f"Rev client - Core responses: {len(rev_core)}, Quote analysis: {len(rev_analysis)}")
        
        # Check default client data
        default_core = db.get_stage1_data_responses(client_id='default')
        default_analysis = db.get_stage2_response_labeling(client_id='default')
        print(f"Default client - Core responses: {len(default_core)}, Quote analysis: {len(default_analysis)}")
        
        # Test the analyzer with Rev client_id
        print("\n🔍 Testing Stage 2 analyzer with client_id='Rev'...")
        analyzer = SupabaseStage2Analyzer()
        
        # Run a small test to see if it uses the correct client_id
        result = analyzer.process_incremental(client_id='Rev')
        
        print(f"✅ Stage 2 result: {result.get('status', 'unknown')}")
        print(f"📊 Quotes processed: {result.get('quotes_processed', 0)}")
        print(f"📊 Quotes analyzed: {result.get('quotes_analyzed', 0)}")
        
        # Check if new analysis data was saved with correct client_id
        print("\n📊 Checking updated data status:")
        
        rev_analysis_after = db.get_stage2_response_labeling(client_id='Rev')
        default_analysis_after = db.get_stage2_response_labeling(client_id='default')
        
        print(f"Rev client - Quote analysis: {len(rev_analysis_after)} (was {len(rev_analysis)})")
        print(f"Default client - Quote analysis: {len(default_analysis_after)} (was {len(default_analysis)})")
        
        # Verify that Rev client data increased and default didn't
        if len(rev_analysis_after) > len(rev_analysis):
            print("✅ SUCCESS: New analysis data was saved with correct client_id='Rev'")
        else:
            print("⚠️ No new analysis data was created (this is normal if all quotes were already analyzed)")
        
        if len(default_analysis_after) == len(default_analysis):
            print("✅ SUCCESS: Default client data remained unchanged")
        else:
            print("❌ WARNING: Default client data changed unexpectedly")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_client_id_fix() 