#!/usr/bin/env python3
"""
Comprehensive analysis of response labeling output quality
"""

import pandas as pd
from supabase_database import SupabaseDatabase

def analyze_response_labeling_quality():
    """Analyze the quality of response labeling output"""
    print("🔍 HARSH EVALUATION OF RESPONSE LABELING OUTPUT")
    print("=" * 60)
    
    # Get data
    db = SupabaseDatabase()
    data = db.get_stage2_response_labeling('Rev')
    
    print(f"\n📊 BASIC METRICS:")
    print(f"Total records: {len(data)}")
    print(f"Records with sentiment: {data['sentiment'].notna().sum()}")
    print(f"Records with relevance scores: {data['relevance_score'].notna().sum()}")
    print(f"Records with confidence scores: {data['confidence'].notna().sum()}")
    print(f"Records with priority scores: {data['priority'].notna().sum()}")
    
    print(f"\n🎯 CRITICAL ISSUES:")
    
    # Issue 1: Missing relevance scores
    missing_relevance = data['relevance_score'].isna().sum()
    print(f"❌ CRITICAL: {missing_relevance}/{len(data)} records missing relevance scores ({(missing_relevance/len(data)*100):.1f}%)")
    
    # Issue 2: Over-reliance on product_capability
    product_capability_count = data[data['criterion'] == 'product_capability'].shape[0]
    product_capability_pct = (product_capability_count/len(data)*100)
    print(f"❌ CRITICAL: {product_capability_count}/{len(data)} records mapped to product_capability ({product_capability_pct:.1f}%) - OVER-RELIANCE")
    
    # Issue 3: Neutral sentiment dominance
    neutral_count = data[data['sentiment'] == 'neutral'].shape[0]
    neutral_pct = (neutral_count/len(data)*100)
    print(f"❌ CRITICAL: {neutral_count}/{len(data)} records have neutral sentiment ({neutral_pct:.1f}%) - LACKS NUANCE")
    
    # Issue 4: Missing criteria coverage
    print(f"\n📋 CRITERIA COVERAGE ANALYSIS:")
    criteria_counts = data['criterion'].value_counts()
    all_criteria = [
        'product_capability', 'customer_support_experience', 'speed_responsiveness',
        'cost_value_proposition', 'scalability_growth', 'integration_technical_fit',
        'security_compliance', 'implementation_onboarding', 'sales_experience_partnership',
        'market_position_reputation', 'commercial_terms'
    ]
    
    for crit in all_criteria:
        count = criteria_counts.get(crit, 0)
        pct = (count/len(data)*100)
        if count == 0:
            print(f"   ❌ {crit}: {count} records ({pct:.1f}%) - COMPLETELY MISSING")
        elif pct < 5:
            print(f"   ⚠️  {crit}: {count} records ({pct:.1f}%) - UNDER-REPRESENTED")
        elif pct > 50:
            print(f"   ⚠️  {crit}: {count} records ({pct:.1f}%) - OVER-REPRESENTED")
        else:
            print(f"   ✅ {crit}: {count} records ({pct:.1f}%)")
    
    print(f"\n🎭 SENTIMENT ANALYSIS:")
    sentiment_counts = data['sentiment'].value_counts()
    for sentiment, count in sentiment_counts.items():
        pct = (count/len(data)*100)
        if sentiment == 'neutral' and pct > 70:
            print(f"   ❌ {sentiment}: {count} records ({pct:.1f}%) - TOO MANY NEUTRAL")
        elif sentiment in ['positive', 'negative'] and pct < 10:
            print(f"   ⚠️  {sentiment}: {count} records ({pct:.1f}%) - TOO FEW")
        else:
            print(f"   ✅ {sentiment}: {count} records ({pct:.1f}%)")
    
    print(f"\n🎯 QUALITY METRICS:")
    high_confidence = data[data['confidence'] == 'high'].shape[0]
    high_confidence_pct = (high_confidence/len(data)*100)
    print(f"High confidence records: {high_confidence}/{len(data)} ({high_confidence_pct:.1f}%)")
    
    high_priority = data[data['priority'] == 'high'].shape[0]
    high_priority_pct = (high_priority/len(data)*100)
    print(f"High priority records: {high_priority}/{len(data)} ({high_priority_pct:.1f}%)")
    
    print(f"\n📈 GRADE ASSESSMENT:")
    
    # Calculate overall grade
    grade_points = 0
    max_points = 100
    
    # Relevance scores (30 points)
    if missing_relevance == 0:
        grade_points += 30
    else:
        grade_points += 30 * (1 - missing_relevance/len(data))
    
    # Criteria distribution (25 points)
    if product_capability_pct < 40:
        grade_points += 25
    else:
        grade_points += 25 * (40/product_capability_pct)
    
    # Sentiment distribution (25 points)
    if neutral_pct < 60:
        grade_points += 25
    else:
        grade_points += 25 * (60/neutral_pct)
    
    # Confidence quality (20 points)
    if high_confidence_pct > 20:
        grade_points += 20
    else:
        grade_points += 20 * (high_confidence_pct/20)
    
    grade_letter = 'A' if grade_points >= 90 else 'B' if grade_points >= 80 else 'C' if grade_points >= 70 else 'D' if grade_points >= 60 else 'F'
    
    print(f"Overall Grade: {grade_letter} ({grade_points:.1f}/100)")
    
    return data, grade_points, grade_letter

if __name__ == "__main__":
    data, grade_points, grade_letter = analyze_response_labeling_quality() 