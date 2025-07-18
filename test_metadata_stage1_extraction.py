#!/usr/bin/env python3
"""
Test script to extract Stage 1 data from metadata CSV transcripts
"""

import pandas as pd
import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from voc_pipeline.modular_processor import ModularProcessor
from supabase_database import SupabaseDatabase
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_metadata_stage1_extraction():
    """Test Stage 1 extraction from metadata CSV for first few rows"""
    
    # Read the metadata CSV
    metadata_file = "Context/Buried Wins Interviews (2).csv"
    logger.info(f"Reading metadata from {metadata_file}")
    
    try:
        df = pd.read_csv(metadata_file)
        logger.info(f"Found {len(df)} rows in metadata CSV")
    except Exception as e:
        logger.error(f"Failed to read metadata CSV: {e}")
        return False
    
    # Check if Raw Transcript column exists
    if 'Raw Transcript' not in df.columns:
        logger.error("Raw Transcript column not found in metadata CSV")
        logger.info(f"Available columns: {list(df.columns)}")
        return False
    
    # Filter for Rev client and completed interviews
    rev_data = df[
        (df['Client Name'] == 'Rev') & 
        (df['Interview Status'] == 'Completed') &
        (df['Raw Transcript'].notna()) &
        (df['Raw Transcript'] != '')
    ].copy()
    
    logger.info(f"Found {len(rev_data)} completed Rev interviews with transcripts")
    
    if len(rev_data) == 0:
        logger.error("No Rev interviews with transcripts found")
        return False
    
    # Take first 3 rows for testing
    test_data = rev_data.head(3)
    logger.info(f"Testing with first {len(test_data)} interviews")
    
    # Initialize processor and database
    processor = ModularProcessor()
    db = SupabaseDatabase()
    
    results = []
    
    for idx, row in test_data.iterrows():
        interview_id = row['Interview ID']
        transcript = row['Raw Transcript']
        interviewee_name = row['Interview Contact Full Name']
        company = row['Interview Contact Company Name']
        deal_status = row['Deal Status']
        date_of_interview = row['Completion Date']
        
        logger.info(f"Processing interview {interview_id}: {interviewee_name} from {company}")
        
        try:
            # Create a temporary file with the transcript
            temp_file = f"temp_{interview_id}.txt"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(transcript)
            
            # Run Stage 1 extraction
            logger.info(f"Running Stage 1 extraction for {interview_id}")
            extracted_data = processor.stage1_core_extraction(
                transcript_path=temp_file,
                company=company,
                interviewee=interviewee_name,
                deal_status=deal_status,
                date_of_interview=date_of_interview
            )
            
            if extracted_data:
                logger.info(f"✅ Successfully extracted {len(extracted_data)} responses from {interview_id}")
                
                # Save to database
                for response in extracted_data:
                    response['client_id'] = 'Rev'
                    response['interview_id'] = interview_id
                    response['interviewee_name'] = interviewee_name
                    response['company'] = company
                    response['deal_status'] = deal_status
                    response['date_of_interview'] = date_of_interview
                
                # Save to database
                success_count = 0
                for response in extracted_data:
                    if db.save_core_response(response):
                        success_count += 1
                logger.info(f"✅ Saved {success_count} responses to database for {interview_id}")
                
                results.append({
                    'interview_id': interview_id,
                    'status': 'success',
                    'responses_extracted': len(extracted_data),
                    'responses_saved': success_count
                })
            else:
                logger.error(f"❌ Stage 1 extraction failed for {interview_id} - no data extracted")
                results.append({
                    'interview_id': interview_id,
                    'status': 'failed',
                    'error': 'No data extracted'
                })
            
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
        except Exception as e:
            logger.error(f"❌ Error processing {interview_id}: {e}")
            results.append({
                'interview_id': interview_id,
                'status': 'error',
                'error': str(e)
            })
    
    # Print summary
    logger.info("\n" + "="*50)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("="*50)
    
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] != 'success']
    
    logger.info(f"✅ Successful: {len(successful)}")
    logger.info(f"❌ Failed: {len(failed)}")
    
    if successful:
        total_responses = sum(r['responses_extracted'] for r in successful)
        total_saved = sum(r['responses_saved'] for r in successful)
        logger.info(f"📊 Total responses extracted: {total_responses}")
        logger.info(f"💾 Total responses saved: {total_saved}")
    
    for result in results:
        if result['status'] == 'success':
            logger.info(f"  ✅ {result['interview_id']}: {result['responses_extracted']} responses")
        else:
            logger.info(f"  ❌ {result['interview_id']}: {result['error']}")
    
    return len(successful) > 0

if __name__ == "__main__":
    success = test_metadata_stage1_extraction()
    if success:
        print("\n✅ Test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Test failed!")
        sys.exit(1) 