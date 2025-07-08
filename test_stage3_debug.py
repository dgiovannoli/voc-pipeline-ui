#!/usr/bin/env python3
"""
Debug script to test Stage 3 processing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase_database import SupabaseDatabase
from stage3_findings_analyzer import Stage3FindingsAnalyzer
import pandas as pd

def test_stage3_debug():
    """Debug Stage 3 processing"""
    print("🔍 Stage 3 Debug Test")
    print("=" * 50)
    
    # Initialize database
    db = SupabaseDatabase()
    client_id = 'Rev'
    
    # Test 1: Check existing findings
    print(f"\n📊 Test 1: Check existing findings for client {client_id}")
    print("-" * 40)
    
    existing_findings = db.get_enhanced_findings(client_id=client_id)
    print(f"Existing findings count: {len(existing_findings)}")
    
    if not existing_findings.empty:
        print("Sample existing findings:")
        for i, finding in existing_findings.head(3).iterrows():
            print(f"  - {finding['title']} (Confidence: {finding['enhanced_confidence']:.1f})")
    
    # Test 2: Check scored quotes
    print(f"\n📊 Test 2: Check scored quotes for client {client_id}")
    print("-" * 40)
    
    scored_quotes = db.get_scored_quotes(client_id=client_id)
    print(f"Scored quotes count: {len(scored_quotes)}")
    
    if not scored_quotes.empty:
        print(f"Sample scored quotes:")
        print(f"  - Relevance scores range: {scored_quotes['relevance_score'].min():.1f} to {scored_quotes['relevance_score'].max():.1f}")
        print(f"  - Average relevance score: {scored_quotes['relevance_score'].mean():.1f}")
        print(f"  - Criteria covered: {scored_quotes['criterion'].nunique()}")
    
    # Test 3: Clear existing findings and run fresh
    print(f"\n📊 Test 3: Clear existing findings and run fresh Stage 3")
    print("-" * 40)
    
    # Clear existing findings
    try:
        result = db.supabase.table('enhanced_findings').delete().eq('client_id', client_id).execute()
        print(f"✅ Cleared {len(result.data)} existing findings")
    except Exception as e:
        print(f"❌ Error clearing findings: {e}")
    
    # Run Stage 3
    print("\n🚀 Running Stage 3 analysis...")
    analyzer = Stage3FindingsAnalyzer()
    result = analyzer.process_enhanced_findings(client_id=client_id)
    
    print(f"\n✅ Stage 3 result: {result}")
    
    # Test 4: Check new findings
    print(f"\n📊 Test 4: Check new findings")
    print("-" * 40)
    
    new_findings = db.get_enhanced_findings(client_id=client_id)
    print(f"New findings count: {len(new_findings)}")
    
    if not new_findings.empty:
        print("New findings generated:")
        for i, finding in new_findings.head(5).iterrows():
            print(f"  - {finding['title']} (Confidence: {finding['enhanced_confidence']:.1f})")

if __name__ == "__main__":
    test_stage3_debug() 