#!/usr/bin/env python3

"""
Test single theme import to identify constraint issues
"""

import pandas as pd
import json
import logging
from supabase_database import SupabaseDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_single_import():
    """Test importing themes one by one"""
    
    # Read CSV
    df = pd.read_csv("Context/scorecard_themes (1).csv")
    db = SupabaseDatabase()
    
    successful = 0
    failed = 0
    
    for idx, row in df.iterrows():
        try:
            # Extract data
            theme_title = row['Theme Title']
            criterion = row['Criterion']
            sentiment = row['Sentiment']
            companies = int(row['Companies'])
            quotes = int(row['Quotes'])
            quality_score = float(row['Quality Score'])
            impact_score = float(row['Impact Score'])
            
            # Map sentiment
            sentiment_lower = sentiment.lower()
            if 'positive' in sentiment_lower:
                sentiment = 'positive'
            elif 'negative' in sentiment_lower:
                sentiment = 'negative'
            elif 'neutral' in sentiment_lower:
                sentiment = 'neutral'
            elif 'mixed' in sentiment_lower:
                sentiment = 'mixed'
            else:
                sentiment = 'neutral'
            
            # Create theme object
            theme = {
                'client_id': 'Rev',
                'theme_title': theme_title,
                'scorecard_criterion': criterion,
                'sentiment_direction': sentiment,
                'client_performance_summary': f"Analysis of {criterion} across {companies} companies",
                'supporting_quotes': json.dumps([{"text": f"Sample quote about {criterion}"}]),
                'quote_count': quotes,
                'companies_represented': companies,
                'overall_quality_score': min(quality_score / 5.0, 1.0)
            }
            
            # Try to insert
            response = db.supabase.table('scorecard_themes').insert(theme).execute()
            
            if response.data:
                successful += 1
                print(f"✅ Success: {theme_title} ({sentiment})")
            else:
                failed += 1
                print(f"❌ Failed: {theme_title} ({sentiment})")
                
        except Exception as e:
            failed += 1
            print(f"❌ Error on row {idx}: {e}")
            print(f"   Theme: {row['Theme Title']}")
            print(f"   Sentiment: {sentiment}")
    
    print(f"\n📊 Results: {successful} successful, {failed} failed")

if __name__ == "__main__":
    test_single_import() 