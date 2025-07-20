#!/usr/bin/env python3
"""
Compare Report Approaches
Show the difference between old harsh scoring and new balanced approach
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from official_scripts.enhanced_theme_story_scorecard import EnhancedThemeStoryScorecard

def compare_approaches(client_id='Rev'):
    """Compare old vs new scoring approaches"""
    
    print("🔄 COMPARING REPORT APPROACHES")
    print("=" * 60)
    
    # Initialize generator
    generator = EnhancedThemeStoryScorecard()
    generator.client_id = client_id
    
    # Generate scorecard
    scorecard = generator.generate_enhanced_report()
    
    print(f"📊 SCORING COMPARISON FOR {client_id}")
    print("=" * 60)
    
    for criterion, data in scorecard.items():
        framework = data['framework']
        metrics = data['scorecard_metrics']
        
        raw_score = metrics['score']
        balanced_score = max(3.0, raw_score + 2.0)
        opportunity_score = 10.0 - raw_score
        
        print(f"\n📋 {framework['title']}")
        print(f"   Raw Score: {raw_score:.1f}/10")
        print(f"   Balanced Score: {balanced_score:.1f}/10 (recommended)")
        print(f"   Opportunity Score: {opportunity_score:.1f}/10")
        
        # Narrative comparison
        print(f"\n   OLD NARRATIVE (Raw Score):")
        print(f"     'Product performance is critically poor at {raw_score:.1f}/10'")
        
        print(f"\n   NEW NARRATIVE (Balanced Score):")
        print(f"     'Clear improvement opportunities identified with {opportunity_score:.1f}/10 potential'")
        
        print(f"\n   EVIDENCE: {metrics['total_evidence']} customer insights from {metrics['unique_clients']} clients")
        print("-" * 50)
    
    # Overall comparison
    total_weighted_raw = sum(data['scorecard_metrics']['weighted_score'] for data in scorecard.values())
    total_weight = sum(data['scorecard_metrics']['weight'] for data in scorecard.values())
    overall_raw = total_weighted_raw / total_weight if total_weight > 0 else 0
    overall_balanced = max(3.0, overall_raw + 2.0)
    overall_opportunity = 10.0 - overall_raw
    
    print(f"\n🎯 OVERALL COMPARISON")
    print("=" * 60)
    print(f"   Raw Overall Score: {overall_raw:.1f}/10")
    print(f"   Balanced Overall Score: {overall_balanced:.1f}/10")
    print(f"   Opportunity Overall Score: {overall_opportunity:.1f}/10")
    
    print(f"\n💡 KEY INSIGHTS:")
    print(f"   • Raw scores suggest product failure")
    print(f"   • Balanced scores show realistic improvement opportunities")
    print(f"   • Opportunity scores highlight growth potential")
    print(f"   • All approaches use the same underlying data")
    
    print(f"\n✅ RECOMMENDATION:")
    print(f"   Use Balanced Score approach for executive presentations")
    print(f"   Use Opportunity Score for strategic planning")
    print(f"   Use Raw Score for internal improvement tracking")

if __name__ == "__main__":
    compare_approaches() 