#!/usr/bin/env python3

"""
Debug script for scorecard theme configuration
"""

import os
import sys
import json
import pandas as pd

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stage4b_scorecard_analyzer import Stage4BScorecardAnalyzer
from supabase_database import SupabaseDatabase

def test_config_loading():
    """Test configuration loading"""
    print("🔧 Testing Configuration Loading")
    print("=" * 50)
    
    analyzer = Stage4BScorecardAnalyzer()
    
    print(f"Config loaded: {analyzer.config is not None}")
    print(f"Stage4B config: {analyzer.config.get('stage4b', 'NOT FOUND')}")
    
    if 'stage4b' in analyzer.config:
        stage4b_config = analyzer.config['stage4b']
        print(f"Relevance threshold: {stage4b_config.get('relevance_threshold', 'NOT FOUND')}")
        print(f"Min quotes per theme: {stage4b_config.get('min_quotes_per_theme', 'NOT FOUND')}")
        print(f"Min companies per theme: {stage4b_config.get('min_companies_per_theme', 'NOT FOUND')}")
    else:
        print("❌ Stage4B configuration not found")
        return False
    
    return True

def test_database_connection():
    """Test database connection"""
    print("\n🗄️ Testing Database Connection")
    print("=" * 50)
    
    db = SupabaseDatabase()
    
    try:
        # Test quote analysis data
        quote_df = db.get_quote_analysis(client_id='Rev')
        print(f"✅ Quote analysis data: {len(quote_df)} records")
        
        if not quote_df.empty:
            print(f"   Columns: {list(quote_df.columns)}")
            print(f"   Criteria: {quote_df['criterion'].unique()}")
            print(f"   Relevance scores: {quote_df['relevance_score'].describe()}")
        
        # Test core responses data
        core_df = db.get_core_responses(client_id='Rev')
        print(f"✅ Core responses data: {len(core_df)} records")
        
        if not core_df.empty:
            print(f"   Columns: {list(core_df.columns)}")
            print(f"   Companies: {core_df['company'].nunique()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def test_criteria_prioritization_simple():
    """Test simple criteria prioritization without LLM"""
    print("\n🎯 Testing Simple Criteria Prioritization")
    print("=" * 50)
    
    db = SupabaseDatabase()
    
    try:
        # Get data
        quote_df = db.get_quote_analysis(client_id='Rev')
        core_df = db.get_core_responses(client_id='Rev')
        
        if quote_df.empty or core_df.empty:
            print("❌ No data available")
            return False
        
        # Merge data
        merged_df = pd.merge(
            quote_df, 
            core_df[['response_id', 'company', 'deal_status']], 
            left_on='quote_id', 
            right_on='response_id', 
            how='left'
        )
        
        print(f"✅ Merged data: {len(merged_df)} records")
        
        # Simple criteria analysis
        criteria_summary = {}
        
        for criterion in merged_df['criterion'].unique():
            criterion_data = merged_df[merged_df['criterion'] == criterion]
            
            high_relevance_quotes = len(criterion_data[criterion_data['relevance_score'] >= 4.0])
            total_quotes = len(criterion_data)
            companies_affected = criterion_data['company'].nunique()
            
            criteria_summary[criterion] = {
                'high_relevance_quotes': high_relevance_quotes,
                'total_quotes': total_quotes,
                'companies_affected': companies_affected,
                'relevance_ratio': high_relevance_quotes / total_quotes if total_quotes > 0 else 0
            }
        
        # Show top criteria
        ranked_criteria = sorted(
            criteria_summary.items(), 
            key=lambda x: x[1]['high_relevance_quotes'], 
            reverse=True
        )
        
        print("\n📊 Top Criteria by High Relevance Quotes:")
        for i, (criterion, data) in enumerate(ranked_criteria[:5], 1):
            print(f"{i}. {criterion}")
            print(f"   High relevance: {data['high_relevance_quotes']}")
            print(f"   Total quotes: {data['total_quotes']}")
            print(f"   Companies: {data['companies_affected']}")
            print(f"   Relevance ratio: {data['relevance_ratio']:.1%}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Criteria prioritization error: {e}")
        return False

def test_database_tables():
    """Test if new database tables exist"""
    print("\n🗄️ Testing Database Tables")
    print("=" * 50)
    
    db = SupabaseDatabase()
    
    tables_to_test = [
        'scorecard_themes',
        'criteria_prioritization', 
        'enhanced_theme_synthesis'
    ]
    
    for table in tables_to_test:
        try:
            response = db.supabase.table(table).select('count').limit(1).execute()
            print(f"✅ {table}: Table exists")
        except Exception as e:
            print(f"❌ {table}: {e}")

def main():
    """Run all debug tests"""
    print("🚀 DEBUG: Scorecard Theme Development")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Configuration
    results['config'] = test_config_loading()
    
    # Test 2: Database connection
    results['database'] = test_database_connection()
    
    # Test 3: Database tables
    test_database_tables()
    
    # Test 4: Simple criteria prioritization
    if results['database']:
        results['criteria'] = test_criteria_prioritization_simple()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 DEBUG SUMMARY")
    print("=" * 60)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test}: {status}")
    
    success_count = sum(results.values())
    total_tests = len(results)
    
    print(f"\n🎉 Overall: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("✅ All tests passed! Ready to run full analysis.")
    else:
        print("⚠️ Some tests failed. Please fix issues before proceeding.")

if __name__ == "__main__":
    main() 