"""
Debug script to examine Stage 2 data structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from official_scripts.database.supabase_database import SupabaseDatabase

def debug_stage2_data():
    """
    Debug Stage 2 data structure
    """
    print("🔍 DEBUGGING STAGE 2 DATA STRUCTURE")
    print("=" * 50)
    
    db = SupabaseDatabase()
    
    # Get Stage 2 data
    stage2_data = db.get_stage2_response_labeling(client_id='Rev')
    print(f"📊 Retrieved {len(stage2_data)} Stage 2 analyses")
    
    if not stage2_data.empty:
        # Show column names
        print(f"\n📋 COLUMN NAMES:")
        for col in stage2_data.columns:
            print(f"   - {col}")
        
        # Show sample data
        print(f"\n📊 SAMPLE DATA (first 3 rows):")
        for i, row in stage2_data.head(3).iterrows():
            print(f"\n   Row {i}:")
            for col in stage2_data.columns:
                value = row.get(col, 'N/A')
                print(f"      {col}: {value}")
        
        # Check sentiment scores
        if 'sentiment_score' in stage2_data.columns:
            sentiment_scores = stage2_data['sentiment_score'].dropna()
            print(f"\n📈 SENTIMENT SCORES:")
            print(f"   Count: {len(sentiment_scores)}")
            print(f"   Range: {sentiment_scores.min()} to {sentiment_scores.max()}")
            print(f"   Mean: {sentiment_scores.mean():.2f}")
            print(f"   Values: {sentiment_scores.unique()}")
        
        # Check business impact
        if 'business_impact' in stage2_data.columns:
            business_impacts = stage2_data['business_impact'].dropna()
            print(f"\n💼 BUSINESS IMPACT:")
            print(f"   Count: {len(business_impacts)}")
            print(f"   Values: {business_impacts.unique()}")
            print(f"   Distribution: {business_impacts.value_counts().to_dict()}")
        
        # Check relevance scores
        if 'relevance_score' in stage2_data.columns:
            relevance_scores = stage2_data['relevance_score'].dropna()
            print(f"\n🎯 RELEVANCE SCORES:")
            print(f"   Count: {len(relevance_scores)}")
            print(f"   Range: {relevance_scores.min()} to {relevance_scores.max()}")
            print(f"   Mean: {relevance_scores.mean():.2f}")
        
        # Check criteria
        if 'criterion' in stage2_data.columns:
            criteria = stage2_data['criterion'].dropna()
            print(f"\n📋 CRITERIA:")
            print(f"   Count: {len(criteria)}")
            print(f"   Values: {criteria.unique()}")
            print(f"   Distribution: {criteria.value_counts().to_dict()}")
        
        # Test filtering logic
        print(f"\n🧪 TESTING FILTERING LOGIC:")
        
        # Count quotes that would pass improvement opportunity filter
        improvement_candidates = 0
        winning_candidates = 0
        
        for _, row in stage2_data.iterrows():
            sentiment_score = row.get('sentiment_score', 0.5) or 0.5
            business_impact = row.get('business_impact', 'medium') or 'medium'
            relevance_score = row.get('relevance_score', 0.5) or 0.5
            
            # Calculate priority score
            impact_weights = {'high': 3.0, 'medium': 2.0, 'low': 1.0}
            impact_weight = impact_weights.get(business_impact, 2.0)
            priority_score = (sentiment_score * 0.3 + relevance_score * 0.4 + impact_weight * 0.3) * 10
            
            # Check improvement opportunity filter
            if (sentiment_score < 0.5 and 
                priority_score >= 3.0 and 
                business_impact in ['high', 'medium']):
                improvement_candidates += 1
            
            # Check winning factor filter
            if (sentiment_score > 0.6 and 
                priority_score >= 3.0 and 
                business_impact in ['high', 'medium']):
                winning_candidates += 1
        
        print(f"   Improvement candidates: {improvement_candidates}")
        print(f"   Winning candidates: {winning_candidates}")
        
        # Show some examples
        print(f"\n📝 EXAMPLE QUOTES:")
        for i, row in stage2_data.head(5).iterrows():
            sentiment_score = row.get('sentiment_score', 0.5) or 0.5
            business_impact = row.get('business_impact', 'medium') or 'medium'
            relevance_score = row.get('relevance_score', 0.5) or 0.5
            
            impact_weights = {'high': 3.0, 'medium': 2.0, 'low': 1.0}
            impact_weight = impact_weights.get(business_impact, 2.0)
            priority_score = (sentiment_score * 0.3 + relevance_score * 0.4 + impact_weight * 0.3) * 10
            
            print(f"\n   Quote {i}:")
            print(f"      Sentiment: {sentiment_score}")
            print(f"      Business Impact: {business_impact}")
            print(f"      Relevance: {relevance_score}")
            print(f"      Priority Score: {priority_score:.1f}")
            print(f"      Would be improvement: {sentiment_score < 0.5 and priority_score >= 3.0 and business_impact in ['high', 'medium']}")
            print(f"      Would be winning: {sentiment_score > 0.6 and priority_score >= 3.0 and business_impact in ['high', 'medium']}")
    
    else:
        print("❌ No Stage 2 data found")

if __name__ == "__main__":
    debug_stage2_data() 