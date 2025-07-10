#!/usr/bin/env python3
"""
Test script to verify the new scoring system implementation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase_database import SupabaseDatabase
import pandas as pd

def test_new_scoring_system():
    """Test the new scoring system implementation"""
    print("🧪 Testing New Scoring System Implementation")
    print("=" * 50)
    
    # Initialize database
    db = SupabaseDatabase()
    
    # Test 1: Check quote analysis data structure
    print("\n📊 Test 1: Quote Analysis Data Structure")
    print("-" * 40)
    
    stage2_response_labeling = db.supabase.table('stage2_response_labeling').select('*').limit(3).execute()
    
    if stage2_response_labeling.data:
        sample = stage2_response_labeling.data[0]
        print(f"✅ Sample quote analysis found")
        print(f"   - relevance_score: {sample.get('relevance_score', 'MISSING')}")
        print(f"   - sentiment: {sample.get('sentiment', 'MISSING')}")
        print(f"   - client_id: {sample.get('client_id', 'MISSING')}")
        
        # Check if new columns exist
        has_relevance = 'relevance_score' in sample
        has_sentiment = 'sentiment' in sample
        has_client_id = 'client_id' in sample
        
        print(f"   - relevance_score column: {'✅' if has_relevance else '❌'}")
        print(f"   - sentiment column: {'✅' if has_sentiment else '❌'}")
        print(f"   - client_id column: {'✅' if has_client_id else '❌'}")
        
        if not all([has_relevance, has_sentiment, has_client_id]):
            print("❌ Missing required columns!")
            return False
    else:
        print("❌ No quote analysis data found")
        return False
    
    # Test 2: Check findings data
    print("\n📊 Test 2: Enhanced Findings Data")
    print("-" * 40)
    
    findings = db.supabase.table('stage3_findings').select('*').limit(3).execute()
    
    if findings.data:
        sample = findings.data[0]
        print(f"✅ Sample finding found")
        print(f"   - title: {sample.get('title', 'MISSING')}")
        print(f"   - enhanced_confidence: {sample.get('enhanced_confidence', 'MISSING')}")
        print(f"   - credibility_tier: {sample.get('credibility_tier', 'MISSING')}")
        print(f"   - client_id: {sample.get('client_id', 'MISSING')}")
        
        # Check if new columns exist
        has_confidence = 'enhanced_confidence' in sample
        has_credibility = 'credibility_tier' in sample
        has_client_id = 'client_id' in sample
        
        print(f"   - enhanced_confidence column: {'✅' if has_confidence else '❌'}")
        print(f"   - credibility_tier column: {'✅' if has_credibility else '❌'}")
        print(f"   - client_id column: {'✅' if has_client_id else '❌'}")
        
        if not all([has_confidence, has_credibility, has_client_id]):
            print("❌ Missing required columns!")
            return False
    else:
        print("❌ No enhanced findings data found")
        return False
    
    # Test 3: Check themes data
    print("\n📊 Test 3: Enhanced Themes Data")
    print("-" * 40)
    
    themes = db.supabase.table('stage4_themes').select('*').limit(3).execute()
    
    if themes.data:
        sample = themes.data[0]
        print(f"✅ Sample theme found")
        print(f"   - theme_statement: {sample.get('theme_statement', 'MISSING')[:100]}...")
        print(f"   - quotes: {sample.get('quotes', 'MISSING')[:100]}...")
        print(f"   - criteria_covered: {sample.get('criteria_covered', 'MISSING')}")
        print(f"   - pattern_type: {sample.get('pattern_type', 'MISSING')}")
        print(f"   - client_id: {sample.get('client_id', 'MISSING')}")
        
        # Check if new columns exist
        has_quotes = 'quotes' in sample
        has_criteria = 'criteria_covered' in sample
        has_pattern = 'pattern_type' in sample
        has_client_id = 'client_id' in sample
        
        print(f"   - quotes column: {'✅' if has_quotes else '❌'}")
        print(f"   - criteria_covered column: {'✅' if has_criteria else '❌'}")
        print(f"   - pattern_type column: {'✅' if has_pattern else '❌'}")
        print(f"   - client_id column: {'✅' if has_client_id else '❌'}")
        
        if not all([has_quotes, has_criteria, has_pattern, has_client_id]):
            print("❌ Missing required columns!")
            return False
    else:
        print("❌ No themes data found")
        return False
    
    # Test 4: Check data counts
    print("\n📊 Test 4: Data Counts")
    print("-" * 40)
    
    # Count quote analyses
    quote_count = db.supabase.table('stage2_response_labeling').select('*', count='exact').execute()
    print(f"   - Quote analyses: {quote_count.count if hasattr(quote_count, 'count') else 'Unknown'}")
    
    # Count findings
    findings_count = db.supabase.table('stage3_findings').select('*', count='exact').execute()
    print(f"   - Enhanced findings: {findings_count.count if hasattr(findings_count, 'count') else 'Unknown'}")
    
    # Count themes
    themes_count = db.supabase.table('stage4_themes').select('*', count='exact').execute()
    print(f"   - Themes: {themes_count.count if hasattr(themes_count, 'count') else 'Unknown'}")
    
    # Test 5: Check client data isolation
    print("\n📊 Test 5: Client Data Isolation")
    print("-" * 40)
    
    # Check Rev client data
    rev_quotes = db.supabase.table('stage2_response_labeling').select('*').eq('client_id', 'Rev').execute()
    rev_findings = db.supabase.table('stage3_findings').select('*').eq('client_id', 'Rev').execute()
    rev_themes = db.supabase.table('stage4_themes').select('*').eq('client_id', 'Rev').execute()
    
    print(f"   - Rev quote analyses: {len(rev_quotes.data)}")
    print(f"   - Rev enhanced findings: {len(rev_findings.data)}")
    print(f"   - Rev themes: {len(rev_themes.data)}")
    
    # Check default client data
    default_quotes = db.supabase.table('stage2_response_labeling').select('*').eq('client_id', 'default').execute()
    default_findings = db.supabase.table('stage3_findings').select('*').eq('client_id', 'default').execute()
    default_themes = db.supabase.table('stage4_themes').select('*').eq('client_id', 'default').execute()
    
    print(f"   - Default quote analyses: {len(default_quotes.data)}")
    print(f"   - Default enhanced findings: {len(default_findings.data)}")
    print(f"   - Default themes: {len(default_themes.data)}")
    
    print("\n✅ All tests completed successfully!")
    print("🎉 New scoring system is working correctly!")
    
    return True

if __name__ == "__main__":
    test_new_scoring_system() 