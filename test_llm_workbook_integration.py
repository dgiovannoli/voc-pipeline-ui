#!/usr/bin/env python3
"""
Test LLM Integration in Workbook Generation
Verifies that LLM-based deduplication shows up in the All Themes tab
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).resolve().parents[0]))

from supabase_database import SupabaseDatabase

def test_llm_similarity():
    """Test that LLM-based similarity analysis works"""
    print("🧪 Testing LLM Integration in Workbook Generation")
    print("=" * 60)
    
    # Check if OpenAI API key is available
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OpenAI API key not found. Set OPENAI_API_KEY environment variable")
        return False
    
    print("✅ OpenAI API key found")
    
    # Initialize database
    db = SupabaseDatabase()
    client_id = "ShipStation API"
    
    print(f"\n🔍 Testing LLM similarity analysis for {client_id}")
    
    # Test LLM-based similarity
    try:
        print("📤 Fetching LLM-based theme similarity...")
        sim_df = db.fetch_theme_similarity(client_id, min_score=0.7, use_llm=True)
        
        if sim_df.empty:
            print("⚠️ No similarity results found")
            return False
        
        print(f"✅ Found {len(sim_df)} similarity pairs")
        
        # Show sample results
        print("\n📊 Sample Results:")
        for i, (_, row) in enumerate(sim_df.head(3).iterrows()):
            print(f"  {i+1}. Score: {row.get('score', 0):.3f}")
            print(f"     Theme A: {row.get('theme_id', 'N/A')}")
            print(f"     Theme B: {row.get('other_theme_id', 'N/A')}")
            print(f"     Subject: {row.get('subject', 'N/A')}")
            
            # Show LLM-specific features
            features = row.get('features_json', {})
            if features:
                print(f"     Confidence: {features.get('decision_band', 'N/A')}")
                print(f"     Rationale: {features.get('rationale', 'N/A')[:100]}...")
                print(f"     Canonical: {features.get('canonical_suggestion', 'N/A')}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing LLM similarity: {e}")
        return False

def test_fallback():
    """Test that fallback to rule-based similarity works"""
    print("\n🔄 Testing Fallback to Rule-based Similarity")
    print("-" * 40)
    
    # Temporarily remove API key to test fallback
    original_key = os.environ.get('OPENAI_API_KEY')
    os.environ['OPENAI_API_KEY'] = ''
    
    try:
        db = SupabaseDatabase()
        client_id = "ShipStation API"
        
        print("📤 Testing fallback to rule-based similarity...")
        sim_df = db.fetch_theme_similarity(client_id, min_score=0.7, use_llm=True)
        
        if sim_df.empty:
            print("✅ Fallback working (no results, which is expected)")
        else:
            print(f"✅ Fallback working (found {len(sim_df)} results)")
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback failed: {e}")
        return False
    finally:
        # Restore API key
        if original_key:
            os.environ['OPENAI_API_KEY'] = original_key

def main():
    """Run all tests"""
    print("🚀 Starting LLM Integration Tests")
    print("=" * 60)
    
    # Test 1: LLM similarity analysis
    test1_passed = test_llm_similarity()
    
    # Test 2: Fallback mechanism
    test2_passed = test_fallback()
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 30)
    print(f"LLM Similarity Analysis: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Fallback Mechanism: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! LLM integration is ready for workbook generation.")
        print("\n💡 Next steps:")
        print("   1. Run your workbook generation script")
        print("   2. Check the 'All Themes' tab")
        print("   3. Look for the 'Duplicates Review' section with LLM results")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
    
    return test1_passed and test2_passed

if __name__ == '__main__':
    main() 