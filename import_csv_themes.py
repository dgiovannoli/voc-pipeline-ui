#!/usr/bin/env python3
"""
Import CSV themes into database for testing semantic merging
"""

import pandas as pd
import logging
from supabase_database import create_supabase_database

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def import_csv_themes():
    """Import themes from CSV into database"""
    try:
        # Read CSV
        csv_path = "Context/scorecard_themes (1).csv"
        df = pd.read_csv(csv_path)
        
        logger.info(f"Loaded {len(df)} themes from CSV")
        
        # Map CSV columns to database columns
        df_mapped = df.copy()
        df_mapped['theme_title'] = df['Theme Title']
        df_mapped['scorecard_criterion'] = df['Criterion']
        df_mapped['sentiment_direction'] = df['Sentiment'].map({
            'terms_neutral': 'mixed',
            'terms_positive': 'positive', 
            'onboarding_neutral': 'mixed',
            'onboarding_positive': 'positive',
            'capability_positive': 'positive',
            'capability_neutral': 'mixed',
            'experience_partnership_positive': 'positive',
            'experience_partnership_neutral': 'mixed',
            'service_quality_neutral': 'mixed',
            'service_quality_positive': 'positive',
            'responsiveness_positive': 'positive',
            'responsiveness_neutral': 'mixed',
            'compliance_neutral': 'mixed',
            'compliance_positive': 'positive',
            'position_reputation_neutral': 'mixed',
            'position_reputation_positive': 'positive',
            'technical_fit_neutral': 'mixed',
            'technical_fit_positive': 'positive',
            'stability_neutral': 'mixed'
        })
        df_mapped['companies_represented'] = df['Companies']
        df_mapped['quotes_count'] = df['Quotes']
        df_mapped['overall_quality_score'] = df['Quality Score']
        
        # Add required column with default value
        df_mapped['client_performance_summary'] = ''
        
        # Connect to database
        supabase_db = create_supabase_database()
        
        # Clear existing themes
        supabase_db.supabase.table('scorecard_themes').delete().neq('id', 0).execute()
        
        # Prepare data for insertion
        themes_data = df_mapped[[
            'theme_title', 'scorecard_criterion', 'sentiment_direction', 
            'companies_represented', 'overall_quality_score', 'client_performance_summary'
        ]].to_dict('records')
        
        # Insert themes
        response = supabase_db.supabase.table('scorecard_themes').insert(themes_data).execute()
        
        if response.data:
            logger.info(f"✅ Successfully imported {len(response.data)} themes to database")
            return True
        else:
            logger.error("❌ No themes were imported")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error importing themes: {e}")
        return False

def main():
    """Main function"""
    logger.info("🚀 Importing CSV themes to database")
    logger.info("=" * 40)
    
    success = import_csv_themes()
    
    if success:
        print("✅ CSV themes imported successfully!")
        print("You can now run: python semantic_theme_merger.py")
    else:
        print("❌ Failed to import CSV themes")

if __name__ == "__main__":
    main() 