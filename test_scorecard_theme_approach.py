#!/usr/bin/env python3

"""
Test Script for Scorecard-Driven Theme Development Approach

This script demonstrates the new Stage 4B approach that complements
the existing similarity-based theme generation.
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stage4b_scorecard_analyzer import Stage4BScorecardAnalyzer
from enhanced_theme_synthesizer import EnhancedThemeSynthesizer
from supabase_database import SupabaseDatabase

def test_criteria_prioritization():
    """Test criteria prioritization analysis"""
    print("🎯 Testing Criteria Prioritization Analysis")
    print("=" * 60)
    
    analyzer = Stage4BScorecardAnalyzer()
    
    # Test with 'Rev' client data
    criteria_prioritization = analyzer.analyze_criteria_prioritization('Rev')
    
    if not criteria_prioritization:
        print("❌ No criteria prioritization data found")
        return None
    
    print(f"✅ Analyzed {len(criteria_prioritization)} criteria")
    
    # Show top prioritized criteria
    ranked_criteria = sorted(
        criteria_prioritization.items(), 
        key=lambda x: x[1]['priority_score'], 
        reverse=True
    )
    
    print("\n📊 Top Prioritized Criteria:")
    print("-" * 60)
    for i, (criterion, data) in enumerate(ranked_criteria[:5], 1):
        print(f"{i}. {criterion}")
        print(f"   Priority Score: {data['priority_score']:.2f}")
        print(f"   High Relevance Quotes: {data['high_relevance_quotes']}")
        print(f"   Companies Affected: {data['companies_affected']}")
        print(f"   Meets Thresholds: {data['meets_prioritization_thresholds']}")
        print()
    
    return criteria_prioritization

def test_scorecard_theme_generation(criteria_prioritization):
    """Test scorecard theme generation"""
    print("🎨 Testing Scorecard Theme Generation")
    print("=" * 60)
    
    analyzer = Stage4BScorecardAnalyzer()
    
    # Generate scorecard themes
    scorecard_themes = analyzer.generate_scorecard_themes(criteria_prioritization, 'Rev')
    
    if not scorecard_themes:
        print("❌ No scorecard themes generated")
        return None
    
    print(f"✅ Generated {len(scorecard_themes)} scorecard themes")
    
    # Show sample themes
    print("\n📋 Sample Scorecard Themes:")
    print("-" * 60)
    for i, theme in enumerate(scorecard_themes[:3], 1):
        print(f"{i}. {theme['theme_title']}")
        print(f"   Criterion: {theme['scorecard_criterion']}")
        print(f"   Sentiment: {theme['sentiment_direction']}")
        print(f"   Performance: {theme['client_performance_summary']}")
        print(f"   Quality Score: {theme['overall_quality_score']:.2f}")
        print(f"   Quotes: {theme['quote_count']}")
        print(f"   Companies: {theme['companies_represented']}")
        print()
    
    return scorecard_themes

def test_enhanced_synthesis():
    """Test enhanced theme synthesis"""
    print("🔄 Testing Enhanced Theme Synthesis")
    print("=" * 60)
    
    synthesizer = EnhancedThemeSynthesizer()
    
    # Run enhanced synthesis
    result = synthesizer.process_enhanced_synthesis('Rev')
    
    if 'error' in result:
        print(f"❌ Error in synthesis: {result['error']}")
        return None
    
    print(f"✅ Enhanced synthesis completed")
    print(f"   Scorecard themes: {len(result['scorecard_themes'])}")
    print(f"   Similarity themes: {len(result['similarity_themes'])}")
    print(f"   Convergence opportunities: {len(result['convergence_opportunities'])}")
    print(f"   Hybrid syntheses: {len(result['hybrid_syntheses'])}")
    print(f"   Total syntheses: {len(result['all_syntheses'])}")
    
    # Show sample syntheses
    print("\n📋 Sample Enhanced Syntheses:")
    print("-" * 60)
    for i, synthesis in enumerate(result['all_syntheses'][:3], 1):
        print(f"{i}. {synthesis['synthesis_title']}")
        print(f"   Type: {synthesis['synthesis_type']}")
        print(f"   Quality: {synthesis['synthesis_quality_score']:.2f}")
        print(f"   Insight: {synthesis['executive_insight'][:100]}...")
        print()
    
    return result

def test_database_integration():
    """Test database integration"""
    print("🗄️ Testing Database Integration")
    print("=" * 60)
    
    db = SupabaseDatabase()
    
    # Test scorecard themes table
    try:
        response = db.supabase.table('scorecard_themes').select('*').eq('client_id', 'Rev').limit(5).execute()
        scorecard_count = len(response.data)
        print(f"✅ Scorecard themes in database: {scorecard_count}")
    except Exception as e:
        print(f"❌ Error accessing scorecard_themes: {e}")
        scorecard_count = 0
    
    # Test criteria prioritization table
    try:
        response = db.supabase.table('criteria_prioritization').select('*').eq('client_id', 'Rev').limit(5).execute()
        criteria_count = len(response.data)
        print(f"✅ Criteria prioritization records: {criteria_count}")
    except Exception as e:
        print(f"❌ Error accessing criteria_prioritization: {e}")
        criteria_count = 0
    
    # Test enhanced theme synthesis table
    try:
        response = db.supabase.table('enhanced_theme_synthesis').select('*').eq('client_id', 'Rev').limit(5).execute()
        synthesis_count = len(response.data)
        print(f"✅ Enhanced syntheses in database: {synthesis_count}")
    except Exception as e:
        print(f"❌ Error accessing enhanced_theme_synthesis: {e}")
        synthesis_count = 0
    
    return {
        'scorecard_themes': scorecard_count,
        'criteria_prioritization': criteria_count,
        'enhanced_syntheses': synthesis_count
    }

def test_quality_metrics():
    """Test quality metrics calculation"""
    print("📊 Testing Quality Metrics")
    print("=" * 60)
    
    # Sample data for testing
    sample_quotes = [
        {
            'text': 'The support team is very responsive',
            'relevance_score': 4.5,
            'sentiment': 'positive',
            'company': 'Company A',
            'interviewee': 'John Doe',
            'deal_status': 'won'
        },
        {
            'text': 'Support responds quickly but lacks proactive guidance',
            'relevance_score': 4.2,
            'sentiment': 'negative',
            'company': 'Company B',
            'interviewee': 'Jane Smith',
            'deal_status': 'lost'
        },
        {
            'text': 'The support quality is excellent',
            'relevance_score': 4.8,
            'sentiment': 'positive',
            'company': 'Company C',
            'interviewee': 'Bob Johnson',
            'deal_status': 'won'
        }
    ]
    
    analyzer = Stage4BScorecardAnalyzer()
    
    # Test quality metrics calculation
    quality_metrics = analyzer._calculate_theme_quality_metrics(sample_quotes, {})
    
    print("Quality Metrics for Sample Theme:")
    print(f"   Evidence Strength: {quality_metrics['evidence_strength']:.2f}")
    print(f"   Sentiment Consistency: {quality_metrics['sentiment_consistency']:.2f}")
    print(f"   Quote Diversity: {quality_metrics['quote_diversity']:.2f}")
    print(f"   Stakeholder Weight: {quality_metrics['stakeholder_weight']:.2f}")
    print(f"   Overall Quality: {quality_metrics['overall_quality']:.2f}")
    
    return quality_metrics

def test_convergence_detection():
    """Test convergence detection between approaches"""
    print("🎯 Testing Convergence Detection")
    print("=" * 60)
    
    # Sample themes for testing
    scorecard_theme = {
        'theme_title': 'Support is Responsive but Not Proactive',
        'scorecard_criterion': 'support_service_quality',
        'sentiment_direction': 'negative',
        'client_performance_summary': 'Support team responds quickly but lacks proactive guidance'
    }
    
    similarity_theme = {
        'theme_statement': 'Customers appreciate quick support responses but want more proactive assistance',
        'theme_category': 'customer_experience',
        'theme_strength': 'High',
        'criteria_covered': ['support_service_quality', 'customer_experience']
    }
    
    synthesizer = EnhancedThemeSynthesizer()
    
    # Test convergence calculation
    convergence_score = synthesizer._calculate_convergence_score(
        scorecard_theme, similarity_theme, 
        {'semantic_similarity_threshold': 0.7, 'criteria_overlap_threshold': 0.5}
    )
    
    convergence_type = synthesizer._determine_convergence_type(scorecard_theme, similarity_theme)
    
    print("Convergence Analysis:")
    print(f"   Scorecard Theme: {scorecard_theme['theme_title']}")
    print(f"   Similarity Theme: {similarity_theme['theme_statement'][:50]}...")
    print(f"   Convergence Score: {convergence_score:.2f}")
    print(f"   Convergence Type: {convergence_type}")
    
    return {
        'convergence_score': convergence_score,
        'convergence_type': convergence_type
    }

def run_comprehensive_test():
    """Run comprehensive test of the scorecard theme approach"""
    print("🚀 COMPREHENSIVE TEST: Scorecard-Driven Theme Development")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    results = {}
    
    # Test 1: Criteria Prioritization
    print("\n" + "="*80)
    results['criteria_prioritization'] = test_criteria_prioritization()
    
    # Test 2: Scorecard Theme Generation
    print("\n" + "="*80)
    if results['criteria_prioritization']:
        results['scorecard_themes'] = test_scorecard_theme_generation(results['criteria_prioritization'])
    
    # Test 3: Enhanced Synthesis
    print("\n" + "="*80)
    results['enhanced_synthesis'] = test_enhanced_synthesis()
    
    # Test 4: Database Integration
    print("\n" + "="*80)
    results['database_integration'] = test_database_integration()
    
    # Test 5: Quality Metrics
    print("\n" + "="*80)
    results['quality_metrics'] = test_quality_metrics()
    
    # Test 6: Convergence Detection
    print("\n" + "="*80)
    results['convergence_detection'] = test_convergence_detection()
    
    # Summary
    print("\n" + "="*80)
    print("📋 TEST SUMMARY")
    print("="*80)
    
    summary = {
        'criteria_prioritization': '✅' if results['criteria_prioritization'] else '❌',
        'scorecard_themes': '✅' if results.get('scorecard_themes') else '❌',
        'enhanced_synthesis': '✅' if results.get('enhanced_synthesis') else '❌',
        'database_integration': '✅' if results.get('database_integration') else '❌',
        'quality_metrics': '✅' if results.get('quality_metrics') else '❌',
        'convergence_detection': '✅' if results.get('convergence_detection') else '❌'
    }
    
    for test, status in summary.items():
        print(f"   {test.replace('_', ' ').title()}: {status}")
    
    # Save results
    with open('scorecard_theme_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Test results saved to: scorecard_theme_test_results.json")
    print(f"🏁 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return results

if __name__ == "__main__":
    # Run comprehensive test
    results = run_comprehensive_test()
    
    # Print final status
    success_count = sum(1 for result in results.values() if result is not None)
    total_tests = len(results)
    
    print(f"\n🎉 Overall Test Status: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("✅ All tests passed! Scorecard theme approach is ready for deployment.")
    else:
        print("⚠️ Some tests failed. Please review the results and fix issues before deployment.") 