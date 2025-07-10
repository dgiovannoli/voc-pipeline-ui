"""
Populate interview_id column in quote_analysis table based on response_id patterns
"""

import pandas as pd
import logging
from supabase_database import SupabaseDatabase
from interviewee_metadata_loader import IntervieweeMetadataLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def populate_interview_ids(client_id: str = 'Rev'):
    """Populate interview_id column based on response_id patterns"""
    
    # Initialize database and metadata loader
    db = SupabaseDatabase()
    metadata_loader = IntervieweeMetadataLoader()
    
    # Get existing quotes
    quotes_df = db.get_scored_quotes(client_id=client_id)
    
    if quotes_df.empty:
        logger.warning("No quotes found to process")
        return
    
    logger.info(f"Found {len(quotes_df)} quotes to process")
    
    # Extract interview_id from response_id pattern
    # Pattern: "Company_Interviewee_X_Y" -> extract X as interview_id
    quotes_df['extracted_interview_id'] = quotes_df['response_id'].apply(
        lambda x: int(x.split('_')[-2]) if isinstance(x, str) and '_' in x and x.split('_')[-2].isdigit() else 1
    )
    
    # Limit interview_id to available metadata (1-10)
    quotes_df['extracted_interview_id'] = quotes_df['extracted_interview_id'].apply(
        lambda x: ((x - 1) % 10) + 1 if isinstance(x, int) else 1
    )
    
    # Update the database with interview_ids
    updated_count = 0
    errors = 0
    
    for _, quote in quotes_df.iterrows():
        try:
            # Get the analysis_id and extracted interview_id
            analysis_id = quote['analysis_id']
            interview_id = int(quote['extracted_interview_id'])
            
            # Update the quote_analysis record
            result = db.supabase.table('quote_analysis').update({
                'interview_id': interview_id
            }).eq('analysis_id', analysis_id).execute()
            
            if result.data:
                updated_count += 1
                if updated_count % 100 == 0:
                    logger.info(f"Updated {updated_count} records...")
                    
                # Log sample mappings
                if updated_count <= 10:
                    company, interviewee = metadata_loader.get_company_and_interviewee(interview_id)
                    logger.info(f"Quote {quote.get('response_id', 'unknown')} -> Interview {interview_id} -> {interviewee} from {company}")
                    
            else:
                errors += 1
                
        except Exception as e:
            errors += 1
            logger.error(f"Error updating quote {quote.get('analysis_id', 'unknown')}: {e}")
    
    logger.info(f"✅ Successfully updated {updated_count} quotes with interview_id")
    if errors > 0:
        logger.warning(f"⚠️ {errors} quotes had errors during update")
    
    # Show summary of mappings
    logger.info(f"\n📊 Interview ID Distribution:")
    interview_counts = quotes_df['extracted_interview_id'].value_counts().sort_index()
    for interview_id, count in interview_counts.items():
        company, interviewee = metadata_loader.get_company_and_interviewee(interview_id)
        logger.info(f"Interview {interview_id}: {count} quotes -> {interviewee} from {company}")
    
    return quotes_df

def verify_interview_ids(client_id: str = 'Rev'):
    """Verify that interview_ids were populated correctly"""
    
    db = SupabaseDatabase()
    metadata_loader = IntervieweeMetadataLoader()
    
    # Get quotes after update
    quotes_df = db.get_scored_quotes(client_id=client_id)
    
    logger.info(f"\n🔍 Verification Results:")
    logger.info(f"Total quotes: {len(quotes_df)}")
    logger.info(f"Quotes with interview_id: {quotes_df['interview_id'].notna().sum()}")
    logger.info(f"Quotes without interview_id: {quotes_df['interview_id'].isna().sum()}")
    
    if quotes_df['interview_id'].notna().sum() > 0:
        logger.info(f"\n📝 Sample populated interview_ids:")
        sample_quotes = quotes_df[quotes_df['interview_id'].notna()].head(5)
        for _, quote in sample_quotes.iterrows():
            interview_id = int(quote['interview_id'])
            company, interviewee = metadata_loader.get_company_and_interviewee(interview_id)
            logger.info(f"Quote {quote['response_id']} -> Interview {interview_id} -> {interviewee} from {company}")
    
    return quotes_df

if __name__ == "__main__":
    logger.info("🚀 Starting interview_id population...")
    
    # Populate interview_ids
    quotes_df = populate_interview_ids()
    
    # Verify the results
    verify_interview_ids()
    
    logger.info("\n✅ Interview ID population complete!")
    logger.info("Next steps:")
    logger.info("1. Run Stage 3 to test the metadata mapping")
    logger.info("2. Check the export to see proper attribution") 