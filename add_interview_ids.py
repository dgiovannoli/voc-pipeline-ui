"""
Script to demonstrate adding interview_id to quotes and testing metadata mapping
"""

import pandas as pd
import logging
from supabase_database import SupabaseDatabase
from interviewee_metadata_loader import IntervieweeMetadataLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_interview_ids_to_quotes(client_id: str = 'Rev'):
    """Add interview_id to quotes for testing metadata mapping"""
    
    # Initialize database and metadata loader
    db = SupabaseDatabase()
    metadata_loader = IntervieweeMetadataLoader()
    
    # Get existing quotes
    quotes_df = db.get_scored_quotes(client_id=client_id)
    
    if quotes_df.empty:
        logger.warning("No quotes found to process")
        return
    
    logger.info(f"Found {len(quotes_df)} quotes to process")
    
    # For demonstration, assign interview_ids based on response_id
    # In practice, you would map based on your actual interview data
    quotes_df['interview_id'] = quotes_df['response_id'].apply(
        lambda x: int(x.split('_')[-1]) if isinstance(x, str) and '_' in x else 1
    )
    
    # Limit interview_id to available metadata (1-10)
    quotes_df['interview_id'] = quotes_df['interview_id'].apply(
        lambda x: ((x - 1) % 10) + 1 if isinstance(x, int) else 1
    )
    
    # Update quotes with interview_id
    updated_count = 0
    for _, quote in quotes_df.iterrows():
        try:
            # Update the quote analysis with interview_id
            quote_data = quote.to_dict()
            quote_data['interview_id'] = int(quote['interview_id'])
            
            # Save back to database (you might need to add this field to your schema)
            # For now, we'll just log the mapping
            interview_id = quote_data['interview_id']
            company, interviewee = metadata_loader.get_company_and_interviewee(interview_id)
            
            logger.info(f"Quote {quote.get('response_id', 'unknown')} -> Interview {interview_id} -> {interviewee} from {company}")
            updated_count += 1
            
        except Exception as e:
            logger.error(f"Error processing quote: {e}")
    
    logger.info(f"✅ Processed {updated_count} quotes with interview_id mapping")
    
    # Show sample mappings
    sample_mappings = quotes_df[['response_id', 'interview_id']].head(10)
    logger.info(f"Sample interview_id mappings:\n{sample_mappings}")
    
    return quotes_df

def test_metadata_mapping():
    """Test the metadata mapping functionality"""
    
    # Initialize metadata loader
    metadata_loader = IntervieweeMetadataLoader()
    
    # Test various interview IDs
    test_ids = [1, 2, 3, 5, 10, 15]  # Some valid, some invalid
    
    logger.info("Testing metadata mapping:")
    for interview_id in test_ids:
        company, interviewee = metadata_loader.get_company_and_interviewee(interview_id)
        valid = metadata_loader.validate_interview_id(interview_id)
        status = "✅ Valid" if valid else "❌ Invalid"
        logger.info(f"Interview {interview_id}: {interviewee} from {company} ({status})")
    
    # Show metadata summary
    summary = metadata_loader.get_metadata_summary()
    logger.info(f"Metadata Summary: {summary}")

if __name__ == "__main__":
    logger.info("🧪 Testing Interview ID and Metadata Mapping Workflow")
    
    # Test metadata mapping
    test_metadata_mapping()
    
    # Add interview IDs to quotes
    logger.info("\n📝 Adding interview_ids to quotes...")
    quotes_df = add_interview_ids_to_quotes()
    
    logger.info("\n✅ Interview ID workflow test complete!")
    logger.info("Next steps:")
    logger.info("1. Add interview_id field to your database schema")
    logger.info("2. Update your quote processing to include interview_id")
    logger.info("3. Run Stage 3 to see the metadata mapping in action") 