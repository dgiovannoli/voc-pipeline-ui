#!/usr/bin/env python3

"""
Test core components without LLM dependencies
"""

import os
import sys
import json
import pandas as pd

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stage4b_scorecard_analyzer import Stage4BScorecardAnalyzer
from enhanced_theme_synthesizer import EnhancedThemeSynthesizer
from supabase_database import SupabaseDatabase

def test_criteria_prioritization():
    """Test criteria prioritization without LLM"""
    print("🎯 Testing Criteria Prioritization")
    print("=" * 50)
    
    analyzer = Stage4BScorecardAnalyzer()
    
    try:
        # Test criteria prioritization
        criteria_prioritization = analyzer.analyze_criteria_prioritization('Rev')
        
        print(f"✅ Analyzed {len(criteria_prioritization)} criteria")
        
        # Show top criteria
        ranked_criteria = sorted(
            criteria_prioritization.items(), 
            key=lambda x: x[1]['priority_score'], 
            reverse=True
        )
        
        print("\n📊 Top Prioritized Criteria:")
        for i, (criterion, data) in enumerate(ranked_criteria[:5], 1):
            print(f"{i}. {criterion}")
            print(f"   Priority Score: {data['priority_score']:.2f}")
            print(f"   High Relevance Quotes: {data['high_relevance_quotes']}")
            print(f"   Companies Affected: {data['companies_affected']}")
            print(f"   Meets Thresholds: {data['meets_prioritization_thresholds']}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_database_integration():
    """Test database integration"""
    print("🗄️ Testing Database Integration")
    print("=" * 50)
    
    db = SupabaseDatabase()
    
    try:
        # Test criteria prioritization table
        response = db.supabase.table('criteria_prioritization').select('*').eq('client_id', 'Rev').limit(5).execute()
        print(f"✅ Criteria prioritization records: {len(response.data)}")
        
        # Test scorecard themes table
        response = db.supabase.table('scorecard_themes').select('*').eq('client_id', 'Rev').limit(5).execute()
        print(f"✅ Scorecard themes records: {len(response.data)}")
        
        # Test enhanced synthesis table
        response = db.supabase.table('enhanced_theme_synthesis').select('*').eq('client_id', 'Rev').limit(5).execute()
        print(f"✅ Enhanced synthesis records: {len(response.data)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_theme_synthesis_logic():
    """Test theme synthesis logic without LLM"""
    print("🔄 Testing Theme Synthesis Logic")
    print("=" * 50)
    
    synthesizer = EnhancedThemeSynthesizer()
    
    try:
        # Get themes for synthesis
        scorecard_themes, similarity_themes = synthesizer.get_themes_for_synthesis('Rev')
        
        print(f"✅ Retrieved {len(scorecard_themes)} scorecard themes and {len(similarity_themes)} similarity themes")
        
        if scorecard_themes and similarity_themes:
            # Test convergence detection
            convergence_opportunities = synthesizer.detect_theme_convergence(scorecard_themes, similarity_themes)
            print(f"✅ Detected {len(convergence_opportunities)} convergence opportunities")
            
            if convergence_opportunities:
                # Show top convergence
                top_convergence = convergence_opportunities[0]
                print(f"\n🎯 Top Convergence:")
                print(f"   Score: {top_convergence['convergence_score']:.2f}")
                print(f"   Type: {top_convergence['convergence_type']}")
                print(f"   Scorecard Theme: {top_convergence['scorecard_theme'].get('theme_title', 'N/A')}")
                print(f"   Similarity Theme: {top_convergence['similarity_theme'].get('theme_statement', 'N/A')[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_quality_metrics():
    """Test quality metrics calculation"""
    print("📊 Testing Quality Metrics")
    print("=" * 50)
    
    analyzer = Stage4BScorecardAnalyzer()
    
    try:
        # Sample quotes for testing
        sample_quotes = [
            {
                'text': 'Sample quote 1',
                'relevance_score': 4.5,
                'sentiment': 'positive',
                'company': 'Company A'
            },
            {
                'text': 'Sample quote 2', 
                'relevance_score': 4.0,
                'sentiment': 'positive',
                'company': 'Company B'
            },
            {
                'text': 'Sample quote 3',
                'relevance_score': 3.5,
                'sentiment': 'neutral',
                'company': 'Company C'
            }
        ]
        
        sample_theme = {
            'theme_title': 'Sample Theme',
            'client_performance_summary': 'Sample summary'
        }
        
        # Calculate quality metrics
        quality_metrics = analyzer._calculate_theme_quality_metrics(sample_quotes, sample_theme)
        
        print("✅ Quality Metrics Calculated:")
        print(f"   Evidence Strength: {quality_metrics['evidence_strength']:.2f}")
        print(f"   Sentiment Consistency: {quality_metrics['sentiment_consistency']:.2f}")
        print(f"   Quote Diversity: {quality_metrics['quote_diversity']:.2f}")
        print(f"   Stakeholder Weight: {quality_metrics['stakeholder_weight']:.2f}")
        print(f"   Overall Quality: {quality_metrics['overall_quality']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all core component tests"""
    print("🚀 CORE COMPONENT TESTING")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Criteria prioritization
    results['criteria_prioritization'] = test_criteria_prioritization()
    
    # Test 2: Database integration
    results['database_integration'] = test_database_integration()
    
    # Test 3: Theme synthesis logic
    results['theme_synthesis'] = test_theme_synthesis_logic()
    
    # Test 4: Quality metrics
    results['quality_metrics'] = test_quality_metrics()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 CORE COMPONENT TEST SUMMARY")
    print("=" * 60)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test}: {status}")
    
    success_count = sum(results.values())
    total_tests = len(results)
    
    print(f"\n🎉 Overall: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("✅ All core components working! LLM integration can be fixed separately.")
    else:
        print("⚠️ Some core components failed. Please fix issues before proceeding.")

if __name__ == "__main__":
    main() 