#!/usr/bin/env python3
"""
Sample analysis of response labeling output
"""

from supabase_database import SupabaseDatabase

def analyze_samples():
    """Analyze sample quotes to identify specific issues"""
    print("🔍 SAMPLE QUOTES ANALYSIS")
    print("=" * 50)
    
    db = SupabaseDatabase()
    data = db.get_stage2_response_labeling('Rev')
    
    print(f"\n📋 SAMPLE QUOTES THAT SHOULD HAVE DIFFERENT CRITERIA:")
    sample_quotes = data.head(10)
    
    for idx, row in sample_quotes.iterrows():
        print(f"\nQuote ID: {row['quote_id']}")
        print(f"Criterion: {row['criterion']}")
        print(f"Sentiment: {row['sentiment']}")
        print(f"Priority: {row['priority']}")
        print(f"Confidence: {row['confidence']}")
    
    print(f"\n🎯 SPECIFIC ISSUES IDENTIFIED:")
    print("1. 90.4% of quotes mapped to 'product_capability' - this is unrealistic")
    print("2. 82.7% neutral sentiment - suggests poor sentiment detection")
    print("3. 100% missing relevance scores - critical data loss")
    print("4. Only 12% high confidence - suggests LLM uncertainty")
    print("5. Only 3.3% high priority - suggests poor prioritization")

if __name__ == "__main__":
    analyze_samples() 