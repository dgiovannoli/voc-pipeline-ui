#!/usr/bin/env python3
"""
Production Metadata Stage 1 Processor
Processes Stage 1 data extraction from metadata CSV files for any client.
"""

import pandas as pd
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from voc_pipeline.modular_processor import ModularProcessor
from supabase_database import SupabaseDatabase

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetadataStage1Processor:
    """Process Stage 1 data extraction from metadata CSV files."""
    
    def __init__(self):
        self.processor = ModularProcessor()
        self.db = SupabaseDatabase()
    
    def process_metadata_csv(self, csv_file_path: str, client_id: str, 
                           transcript_column: str = 'Raw Transcript',
                           max_interviews: Optional[int] = None,
                           dry_run: bool = False) -> Dict[str, any]:
        """
        Process Stage 1 extraction from metadata CSV file.
        
        Args:
            csv_file_path: Path to metadata CSV file
            client_id: Client ID for data siloing
            transcript_column: Name of column containing transcript text
            max_interviews: Maximum number of interviews to process (None for all)
            dry_run: If True, don't save to database, just return results
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"🎯 Starting metadata Stage 1 processing for client: {client_id}")
        logger.info(f"📁 Processing CSV: {csv_file_path}")
        
        # Read metadata CSV
        try:
            df = pd.read_csv(csv_file_path)
            logger.info(f"📊 Found {len(df)} rows in metadata CSV")
        except Exception as e:
            logger.error(f"❌ Failed to read metadata CSV: {e}")
            return {
                'success': False,
                'error': f"Failed to read CSV: {e}",
                'processed': 0,
                'total_responses': 0
            }
        
        # Validate required columns
        required_columns = ['Interview ID', 'Client Name', 'Interview Contact Full Name', 
                          'Interview Contact Company Name', 'Deal Status', 'Completion Date', 'Industry']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"❌ Missing required columns: {missing_columns}")
            return {
                'success': False,
                'error': f"Missing required columns: {missing_columns}",
                'processed': 0,
                'total_responses': 0
            }
        
        if transcript_column not in df.columns:
            logger.error(f"❌ Transcript column '{transcript_column}' not found")
            logger.info(f"Available columns: {list(df.columns)}")
            return {
                'success': False,
                'error': f"Transcript column '{transcript_column}' not found",
                'processed': 0,
                'total_responses': 0
            }
        
        # Filter for target client and completed interviews with transcripts
        target_data = df[
            (df['Client Name'] == client_id) & 
            (df['Interview Status'] == 'Completed') &
            (df[transcript_column].notna()) &
            (df[transcript_column] != '')
        ].copy()
        
        logger.info(f"🎯 Found {len(target_data)} completed {client_id} interviews with transcripts")
        
        if len(target_data) == 0:
            logger.warning(f"⚠️ No completed interviews with transcripts found for client {client_id}")
            return {
                'success': True,
                'processed': 0,
                'total_responses': 0,
                'message': f"No completed interviews with transcripts found for client {client_id}"
            }
        
        # Limit number of interviews if specified
        if max_interviews:
            target_data = target_data.head(max_interviews)
            logger.info(f"🔢 Processing first {len(target_data)} interviews (limited by max_interviews)")
        
        # Process each interview
        results = []
        total_responses = 0
        
        for idx, row in target_data.iterrows():
            interview_id = row['Interview ID']
            transcript = row[transcript_column]
            interviewee_name = row['Interview Contact Full Name']
            company = row['Interview Contact Company Name']
            deal_status = row['Deal Status']
            date_of_interview = row['Completion Date']
            industry = row['Industry']
            
            logger.info(f"📝 Processing interview {interview_id}: {interviewee_name} from {company}")
            
            try:
                # Create temporary file with transcript
                temp_file = f"temp_{interview_id}_{client_id}.txt"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(transcript)
                
                # Run Stage 1 extraction
                extracted_data = self.processor.stage1_core_extraction(
                    transcript_path=temp_file,
                    company=company,
                    interviewee=interviewee_name,
                    deal_status=deal_status,
                    date_of_interview=date_of_interview
                )
                
                if extracted_data:
                    logger.info(f"✅ Successfully extracted {len(extracted_data)} responses from {interview_id}")
                    
                    # Add metadata to each response
                    for response in extracted_data:
                        response['client_id'] = client_id
                        response['interview_id'] = interview_id
                        response['interviewee_name'] = interviewee_name
                        response['company'] = company
                        response['deal_status'] = deal_status
                        response['date_of_interview'] = date_of_interview
                        response['industry'] = industry
                    
                    # Save to database if not dry run
                    if not dry_run:
                        success_count = 0
                        for response in extracted_data:
                            if self.db.save_core_response(response):
                                success_count += 1
                        logger.info(f"💾 Saved {success_count} responses to database for {interview_id}")
                    else:
                        success_count = len(extracted_data)
                        logger.info(f"🔍 DRY RUN: Would save {success_count} responses for {interview_id}")
                    
                    results.append({
                        'interview_id': interview_id,
                        'status': 'success',
                        'responses_extracted': len(extracted_data),
                        'responses_saved': success_count,
                        'interviewee': interviewee_name,
                        'company': company
                    })
                    
                    total_responses += success_count
                else:
                    logger.warning(f"⚠️ No data extracted from {interview_id}")
                    results.append({
                        'interview_id': interview_id,
                        'status': 'no_data',
                        'responses_extracted': 0,
                        'responses_saved': 0,
                        'interviewee': interviewee_name,
                        'company': company
                    })
                
                # Clean up temp file
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
            except Exception as e:
                logger.error(f"❌ Error processing {interview_id}: {e}")
                results.append({
                    'interview_id': interview_id,
                    'status': 'error',
                    'error': str(e),
                    'interviewee': interviewee_name,
                    'company': company
                })
        
        # Generate summary
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] != 'success']
        
        logger.info("\n" + "="*60)
        logger.info("METADATA STAGE 1 PROCESSING SUMMARY")
        logger.info("="*60)
        logger.info(f"📊 Total interviews processed: {len(results)}")
        logger.info(f"✅ Successful: {len(successful)}")
        logger.info(f"❌ Failed/No Data: {len(failed)}")
        logger.info(f"💾 Total responses saved: {total_responses}")
        
        if successful:
            avg_responses = sum(r['responses_extracted'] for r in successful) / len(successful)
            logger.info(f"📈 Average responses per interview: {avg_responses:.1f}")
        
        # Log individual results
        for result in results:
            if result['status'] == 'success':
                logger.info(f"  ✅ {result['interview_id']}: {result['responses_extracted']} responses")
            elif result['status'] == 'no_data':
                logger.info(f"  ⚠️ {result['interview_id']}: No data extracted")
            else:
                logger.info(f"  ❌ {result['interview_id']}: {result.get('error', 'Unknown error')}")
        
        return {
            'success': True,
            'processed': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'total_responses': total_responses,
            'results': results,
            'client_id': client_id,
            'dry_run': dry_run
        }
    
    def get_available_clients(self, csv_file_path: str) -> List[str]:
        """Get list of available clients in the metadata CSV."""
        try:
            df = pd.read_csv(csv_file_path)
            if 'Client Name' not in df.columns:
                return []
            
            clients = df['Client Name'].dropna().unique().tolist()
            return sorted(clients)
        except Exception as e:
            logger.error(f"Error reading CSV for client list: {e}")
            return []
    
    def get_interview_summary(self, csv_file_path: str, client_id: Optional[str] = None) -> Dict[str, any]:
        """Get summary of interviews in the metadata CSV."""
        try:
            df = pd.read_csv(csv_file_path)
            
            if client_id:
                df = df[df['Client Name'] == client_id]
            
            total_interviews = len(df)
            completed_interviews = len(df[df['Interview Status'] == 'Completed'])
            interviews_with_transcripts = len(df[
                (df['Interview Status'] == 'Completed') &
                (df['Raw Transcript'].notna()) &
                (df['Raw Transcript'] != '')
            ])
            
            return {
                'total_interviews': total_interviews,
                'completed_interviews': completed_interviews,
                'interviews_with_transcripts': interviews_with_transcripts,
                'client_id': client_id
            }
        except Exception as e:
            logger.error(f"Error getting interview summary: {e}")
            return {
                'error': str(e),
                'total_interviews': 0,
                'completed_interviews': 0,
                'interviews_with_transcripts': 0
            }

def main():
    """Command line interface for metadata processing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process Stage 1 data from metadata CSV')
    parser.add_argument('csv_file', help='Path to metadata CSV file')
    parser.add_argument('client_id', help='Client ID to process')
    parser.add_argument('--transcript-column', default='Raw Transcript', 
                       help='Name of column containing transcript text')
    parser.add_argument('--max-interviews', type=int, 
                       help='Maximum number of interviews to process')
    parser.add_argument('--dry-run', action='store_true',
                       help='Process without saving to database')
    
    args = parser.parse_args()
    
    processor = MetadataStage1Processor()
    
    # Get summary first
    summary = processor.get_interview_summary(args.csv_file, args.client_id)
    print(f"\n📊 Interview Summary for {args.client_id}:")
    print(f"  Total interviews: {summary['total_interviews']}")
    print(f"  Completed: {summary['completed_interviews']}")
    print(f"  With transcripts: {summary['interviews_with_transcripts']}")
    
    if summary['interviews_with_transcripts'] == 0:
        print(f"\n❌ No interviews with transcripts found for {args.client_id}")
        return
    
    # Process the data
    result = processor.process_metadata_csv(
        csv_file_path=args.csv_file,
        client_id=args.client_id,
        transcript_column=args.transcript_column,
        max_interviews=args.max_interviews,
        dry_run=args.dry_run
    )
    
    if result['success']:
        print(f"\n✅ Processing completed successfully!")
        print(f"📊 Processed {result['processed']} interviews")
        print(f"💾 Saved {result['total_responses']} responses")
    else:
        print(f"\n❌ Processing failed: {result['error']}")

if __name__ == "__main__":
    main() 