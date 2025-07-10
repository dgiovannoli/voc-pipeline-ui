#!/usr/bin/env python3

"""
Import Scorecard Themes from CSV

This script imports scorecard themes from CSV format into the database
with proper formatting and quality scoring.
"""

import pandas as pd
import json
import logging
from typing import List, Dict
from supabase_database import SupabaseDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_scorecard_themes_from_csv(csv_path: str, client_id: str = 'default') -> Dict:
    """Import scorecard themes from CSV file"""
    logger.info(f"📥 Importing scorecard themes from {csv_path}")
    
    try:
        # Read CSV file
        df = pd.read_csv(csv_path)
        logger.info(f"✅ Loaded {len(df)} themes from CSV")
        
        # Validate required columns
        required_columns = ['Theme Title', 'Criterion', 'Sentiment', 'Companies', 'Quotes', 'Quality Score', 'Impact Score']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"❌ Missing required columns: {missing_columns}")
            return {"status": "error", "message": f"Missing columns: {missing_columns}"}
        
        # Process themes
        themes = []
        for idx, row in df.iterrows():
            theme = process_csv_theme(row, client_id)
            if theme:
                themes.append(theme)
        
        logger.info(f"✅ Processed {len(themes)} themes")
        
        # Save to database
        if themes:
            save_success = save_themes_to_database(themes)
            if save_success:
                logger.info("✅ Themes saved to database successfully")
                return {
                    "status": "success",
                    "themes_imported": len(themes),
                    "total_themes": len(df),
                    "processing_errors": len(df) - len(themes)
                }
            else:
                logger.error("❌ Failed to save themes to database")
                return {"status": "save_error", "message": "Failed to save themes"}
        else:
            logger.warning("⚠️ No valid themes to import")
            return {"status": "no_valid_themes", "message": "No valid themes found"}
            
    except Exception as e:
        logger.error(f"❌ Error importing themes: {e}")
        return {"status": "error", "message": str(e)}

def process_csv_theme(row: pd.Series, client_id: str) -> Dict:
    """Process a single CSV theme row"""
    try:
        # Extract basic data
        theme_title = row['Theme Title']
        criterion = row['Criterion']
        sentiment = row['Sentiment']
        companies = int(row['Companies'])
        quotes = int(row['Quotes'])
        quality_score = float(row['Quality Score'])
        impact_score = float(row['Impact Score'])
        
        # Map sentiment to allowed set
        sentiment_lower = sentiment.lower()
        if 'positive' in sentiment_lower:
            sentiment = 'positive'
        elif 'negative' in sentiment_lower:
            sentiment = 'negative'
        elif 'neutral' in sentiment_lower:
            sentiment = 'mixed'
        elif 'mixed' in sentiment_lower:
            sentiment = 'mixed'
        else:
            sentiment = 'mixed'
        
        # Normalize quality score (assuming it's on 0-5 scale, convert to 0-1)
        normalized_quality = min(quality_score / 5.0, 1.0)
        
        # Normalize impact score (assuming it's on 0-5 scale, convert to 0-1)
        normalized_impact = min(impact_score / 5.0, 1.0)
        
        # Generate supporting quotes placeholder
        supporting_quotes = generate_placeholder_quotes(quotes, criterion, sentiment)
        
        # Calculate quality metrics
        quality_metrics = calculate_quality_metrics_from_csv(
            quality_score, impact_score, companies, quotes
        )
        
        # Generate performance summary
        performance_summary = generate_performance_summary_from_csv(
            criterion, sentiment, companies, quality_score
        )
        
        # Create theme object with only existing columns
        theme = {
            'client_id': client_id,
            'theme_title': theme_title,
            'scorecard_criterion': criterion,
            'sentiment_direction': sentiment,
            'client_performance_summary': performance_summary,
            'supporting_quotes': supporting_quotes,
            'quote_count': quotes,
            'companies_represented': companies,
            'overall_quality_score': quality_metrics['overall_quality']
        }
        
        return theme
        
    except Exception as e:
        logger.error(f"Error processing theme row: {e}")
        return None

def generate_placeholder_quotes(quote_count: int, criterion: str, sentiment: str) -> List[Dict]:
    """Generate placeholder quotes for CSV import"""
    quotes = []
    
    for i in range(min(quote_count, 5)):  # Limit to 5 quotes
        quote = {
            'text': f"Sample quote {i+1} about {criterion} with {sentiment} sentiment",
            'relevance_score': 4.0,  # Default high relevance
            'sentiment': sentiment,
            'company': f"Company_{i+1}",
            'deal_status': 'unknown'
        }
        quotes.append(quote)
    
    return quotes

def calculate_quality_metrics_from_csv(quality_score: float, impact_score: float, 
                                     companies: int, quotes: int) -> Dict:
    """Calculate quality metrics from CSV data"""
    
    # Evidence strength (based on quality score)
    evidence_strength = min(quality_score / 5.0, 1.0)
    
    # Sentiment consistency (assume high for CSV data)
    sentiment_consistency = 0.8
    
    # Quote diversity (company representation)
    quote_diversity = min(companies / max(quotes, 1), 1.0)
    
    # Stakeholder weight (based on company count)
    stakeholder_weight = min(companies / 10.0, 1.0)
    
    # Overall quality (weighted average)
    overall_quality = (
        evidence_strength * 0.4 +
        sentiment_consistency * 0.3 +
        quote_diversity * 0.2 +
        stakeholder_weight * 0.1
    )
    
    return {
        'evidence_strength': round(evidence_strength, 3),
        'sentiment_consistency': round(sentiment_consistency, 3),
        'quote_diversity': round(quote_diversity, 3),
        'stakeholder_weight': round(stakeholder_weight, 3),
        'overall_quality': round(overall_quality, 3)
    }

def generate_performance_summary_from_csv(criterion: str, sentiment: str, 
                                        companies: int, quality_score: float) -> str:
    """Generate performance summary from CSV data"""
    
    criterion_map = {
        'commercial': 'commercial terms and pricing',
        'implementation': 'implementation and onboarding processes',
        'product': 'product capabilities and features',
        'sales': 'sales experience and partnership',
        'support': 'support and service quality',
        'speed': 'speed and responsiveness',
        'security': 'security and compliance',
        'market': 'market position and reputation',
        'integration': 'integration and technical fit',
        'vendor': 'vendor stability'
    }
    
    criterion_name = criterion_map.get(criterion, criterion)
    
    if quality_score >= 4.0:
        performance = "excellent"
    elif quality_score >= 3.0:
        performance = "good"
    elif quality_score >= 2.0:
        performance = "mixed"
    else:
        performance = "needs improvement"
    
    summary = f"Analysis of {criterion_name} across {companies} companies shows {performance} performance "
    summary += f"with {sentiment.replace('_', ' ')} sentiment. "
    summary += f"Quality score of {quality_score:.2f} indicates {performance} overall satisfaction."
    
    return summary

def generate_strategic_note_from_csv(criterion: str, quality_score: float) -> str:
    """Generate strategic note from CSV data"""
    
    if quality_score >= 4.0:
        return f"High-performing {criterion} area that represents a competitive strength"
    elif quality_score >= 3.0:
        return f"Solid {criterion} performance with opportunities for enhancement"
    elif quality_score >= 2.0:
        return f"Mixed {criterion} performance requiring strategic attention"
    else:
        return f"Critical {criterion} area requiring immediate strategic investment"

def generate_competitive_positioning_from_csv(sentiment: str) -> str:
    """Generate competitive positioning from CSV data"""
    
    if 'positive' in sentiment:
        return "Competitive strength that differentiates from alternatives"
    elif 'neutral' in sentiment:
        return "Competitive parity with opportunities for differentiation"
    else:
        return "Competitive gap requiring strategic investment"

def save_themes_to_database(themes: List[Dict]) -> bool:
    """Save themes to database"""
    logger.info(f"💾 Saving {len(themes)} themes to database...")
    
    try:
        db = SupabaseDatabase()
        
        # Insert themes in batches
        batch_size = 10
        for i in range(0, len(themes), batch_size):
            batch = themes[i:i + batch_size]
            
            # Convert supporting_quotes to JSON string
            for theme in batch:
                if isinstance(theme['supporting_quotes'], list):
                    theme['supporting_quotes'] = json.dumps(theme['supporting_quotes'])
            
            response = db.supabase.table('scorecard_themes').insert(batch).execute()
            
            if not response.data:
                logger.error(f"Failed to save batch {i//batch_size + 1}")
                return False
        
        logger.info("✅ Themes saved successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error saving themes: {e}")
        return False

def main():
    """Main function"""
    # Import themes from the CSV file
    csv_path = "Context/scorecard_themes (1).csv"
    client_id = "Rev"
    
    result = import_scorecard_themes_from_csv(csv_path, client_id)
    
    print("\n📊 IMPORT RESULTS")
    print("=" * 40)
    print(f"Status: {result['status']}")
    
    if result['status'] == 'success':
        print(f"Themes Imported: {result['themes_imported']}")
        print(f"Total Themes: {result['total_themes']}")
        print(f"Processing Errors: {result['processing_errors']}")
    else:
        print(f"Error: {result['message']}")

if __name__ == "__main__":
    main() 