#!/usr/bin/env python3
"""
Production Metadata Stage 1 Processor
Processes Stage 1 data extraction from metadata CSV files for any client.
Now includes automatic LLM harmonization of subjects.
"""

import pandas as pd
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re
import requests

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from voc_pipeline.modular_processor import ModularProcessor
from supabase_database import SupabaseDatabase

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MetadataStage1Processor:
    """Process Stage 1 data extraction from metadata CSV files with automatic harmonization."""
    
    def __init__(self):
        self.processor = ModularProcessor()
        self.db = SupabaseDatabase()
        
        # Initialize harmonizer
        try:
            from fixed_llm_harmonizer import FixedLLMHarmonizer
            self.harmonizer = FixedLLMHarmonizer()
            logger.info("✅ LLM Harmonizer initialized for auto-harmonization")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize harmonizer: {e}")
            self.harmonizer = None
    
    def process_metadata_csv(self, csv_file_path: str, client_id: str, 
                           transcript_column: str = 'Raw Transcript',
                           max_interviews: Optional[int] = None,
                           dry_run: bool = False,
                           processing_mode: str = "parallel",
                           max_workers: int = 3) -> Dict[str, any]:
        """
        Process Stage 1 extraction from metadata CSV file with automatic harmonization.
        
        Args:
            csv_file_path: Path to metadata CSV file
            client_id: Client ID for data siloing
            transcript_column: Name of column containing transcript text
            max_interviews: Maximum number of interviews to process (None for all)
            dry_run: If True, don't save to database, just return results
            processing_mode: "parallel" or "sequential" processing mode
            max_workers: Number of parallel workers (only used in parallel mode)
            
        Returns:
            Dictionary with processing results including harmonization stats
        """
        logger.info(f"🎯 Starting metadata Stage 1 processing with auto-harmonization for client: {client_id}")
        logger.info(f"📁 Processing CSV: {csv_file_path}")
        logger.info(f"⚡ Processing mode: {processing_mode.upper()}" + (f" ({max_workers} workers)" if processing_mode == "parallel" else ""))
        
        # Read metadata CSV
        try:
            # Check if file exists and has content
            if not os.path.exists(csv_file_path):
                logger.error(f"❌ CSV file does not exist: {csv_file_path}")
                return {
                    'success': False,
                    'error': f"CSV file does not exist: {csv_file_path}",
                    'processed': 0,
                    'total_responses': 0
                }
            
            # Check file size
            file_size = os.path.getsize(csv_file_path)
            if file_size == 0:
                logger.error(f"❌ CSV file is empty: {csv_file_path}")
                return {
                    'success': False,
                    'error': f"CSV file is empty: {csv_file_path}",
                    'processed': 0,
                    'total_responses': 0
                }
            
            logger.info(f"📁 CSV file size: {file_size} bytes")
            
            # Try to read CSV with different encodings
            df = None
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(csv_file_path, encoding=encoding)
                    logger.info(f"✅ Successfully read CSV with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    if "No columns to parse" in str(e):
                        logger.error(f"❌ CSV has no valid columns to parse: {e}")
                        # Try to read as text to see what's in the file
                        try:
                            with open(csv_file_path, 'r', encoding='utf-8') as f:
                                first_lines = f.readlines()[:5]
                            logger.error(f"❌ First 5 lines of file: {first_lines}")
                        except:
                            pass
                        return {
                            'success': False,
                            'error': f"CSV has no valid columns to parse: {e}",
                            'processed': 0,
                            'total_responses': 0
                        }
                    else:
                        continue
            
            if df is None:
                logger.error(f"❌ Failed to read CSV with any encoding")
                return {
                    'success': False,
                    'error': "Failed to read CSV with any encoding",
                    'processed': 0,
                    'total_responses': 0
                }
            
            logger.info(f"📊 Found {len(df)} rows in metadata CSV")
            logger.info(f"📊 CSV columns: {list(df.columns)}")
            
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
        
        # Debug: Show what's in the data
        logger.info(f"🔍 Debug: Client Name values: {df['Client Name'].unique()}")
        logger.info(f"🔍 Debug: Interview Status values: {df['Interview Status'].unique()}")
        logger.info(f"🔍 Debug: Transcript column '{transcript_column}' has {df[transcript_column].notna().sum()} non-null values")
        logger.info(f"🔍 Debug: Transcript column '{transcript_column}' has {len(df[df[transcript_column] != ''])} non-empty values")
        
        # Show sample data for debugging
        logger.info(f"🔍 Debug: Sample data:")
        for idx, row in df.head(3).iterrows():
            transcript_value = row.get(transcript_column, '')
            logger.info(f"  Row {idx}: Client='{row.get('Client Name', 'N/A')}', Status='{row.get('Interview Status', 'N/A')}', TranscriptLength={len(str(transcript_value))}, TranscriptPreview='{str(transcript_value)[:100]}...'")
        
        # Check what's actually in the transcript column
        logger.info(f"🔍 Debug: Transcript column analysis:")
        transcript_values = df[transcript_column].dropna()
        logger.info(f"  Non-null count: {len(transcript_values)}")
        logger.info(f"  Empty string count: {(transcript_values == '').sum()}")
        logger.info(f"  Whitespace-only count: {(transcript_values.astype(str).str.strip() == '').sum()}")
        logger.info(f"  Non-empty count: {(transcript_values.astype(str).str.strip() != '').sum()}")
        
        # Check if there's a Raw Transcript File column that might contain the actual transcripts
        if 'Raw Transcript File' in df.columns:
            logger.info(f"🔍 Debug: Raw Transcript File column analysis:")
            file_values = df['Raw Transcript File'].dropna()
            logger.info(f"  Non-null count: {len(file_values)}")
            logger.info(f"  Sample values: {file_values.head(3).tolist()}")
        
        # Check if there's a Transcript Link column
        if 'Transcript Link' in df.columns:
            logger.info(f"🔍 Debug: Transcript Link column analysis:")
            link_values = df['Transcript Link'].dropna()
            logger.info(f"  Non-null count: {len(link_values)}")
            logger.info(f"  Sample values: {link_values.head(3).tolist()}")
        
        # Prefer 'Raw Transcript' when present; else auto-detect from known candidates
        transcript_columns_to_check = [
            'Raw Transcript',
            'Raw Transcript (Cleaned)',
            'Transcript',
            'Full Transcript',
            'Moderator Responses',
            'Raw Transcript File',
            'Transcript Link'
        ]
        
        actual_transcript_column = None
        # If Raw Transcript exists, use it regardless, but log if mostly URLs
        if 'Raw Transcript' in df.columns:
            actual_transcript_column = 'Raw Transcript'
            non_empty_count = df['Raw Transcript'].dropna().astype(str).str.strip().str.len().gt(0).sum()
            logger.info(f"🔍 Column 'Raw Transcript' selected with {non_empty_count} non-empty values")
        else:
            for col in transcript_columns_to_check:
                if col in df.columns:
                    non_empty_count = df[col].dropna().astype(str).str.strip().str.len().gt(0).sum()
                    logger.info(f"🔍 Column '{col}' has {non_empty_count} non-empty values")
                    if non_empty_count > 0:
                        actual_transcript_column = col
                        logger.info(f"✅ Found transcripts in column: '{col}'")
                        break
        
        # Upsert interview_metadata for ALL rows that belong to this client (regardless of transcript presence)
        try:
            all_client_rows = df[df['__client_name_norm__'] == normalized_client_id].copy()
            meta_upserts = 0
            for _, mrow in all_client_rows.iterrows():
                self.db.upsert_interview_metadata(
                    client_id=client_id,
                    interview_id=mrow.get('Interview ID', ''),
                    interviewee_name=mrow.get('Interview Contact Full Name', ''),
                    company=mrow.get('Interview Contact Company Name', ''),
                    deal_status=mrow.get('Deal Status', ''),
                    date_of_interview=str(mrow.get('Completion Date', '')),
                    industry=mrow.get('Industry', ''),
                    interviewee_role=mrow.get('Interviewee Role', ''),
                    firm_size=str(mrow.get('Firm Size', '')),
                    audio_video_link=mrow.get('Audio/Video Link', ''),
                    contact_website=mrow.get('Interview Contact Website', '')
                )
                meta_upserts += 1
            logger.info(f"💾 Upserted interview_metadata for {meta_upserts} {client_id} rows from CSV")
        except Exception as e:
            logger.warning(f"⚠️ Could not upsert interview_metadata for all client rows: {e}")

        if actual_transcript_column is None:
            logger.warning(f"⚠️ No transcript content found in any column")
            return {
                'success': True,
                'processed': 0,
                'total_responses': 0,
                'message': f"No transcript content found in any column for client {client_id}"
            }
        
        # Filter for target client and completed interviews with transcripts
        # More robust filtering that handles various empty/whitespace cases
        def _normalize_client(s: str) -> str:
            """Normalize client strings by lowercasing and removing non-alphanumerics."""
            return re.sub(r'[^a-z0-9]', '', str(s).lower())
        
        normalized_client_id = _normalize_client(client_id)
        df['__client_name_norm__'] = df['Client Name'].apply(_normalize_client)
        
        target_data = df[
            (df['__client_name_norm__'] == normalized_client_id) & 
            (df['Interview Status'] == 'Completed') &
            (df[actual_transcript_column].notna()) &
            (df[actual_transcript_column].astype(str).str.strip().str.len() > 0)
        ].copy()
        logger.info(f"🎯 Normalized client filter: input='{client_id}' → norm='{normalized_client_id}'. Matches found: {len(target_data)}")
        
        logger.info(f"🎯 Using transcript column: '{actual_transcript_column}'")
        
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
        total_harmonized = 0
        
        for idx, row in target_data.iterrows():
            interview_id = row['Interview ID']
            transcript = row[actual_transcript_column]  # Use the detected column
            # If transcript is a link or file reference in ANY column, attempt to fetch the actual content
            try:
                if isinstance(transcript, str):
                    source_ref = transcript.strip()
                    # Detect Google Docs and convert to export-as-text
                    if source_ref.startswith('http'):
                        if 'docs.google.com/document/d/' in source_ref:
                            import re as _re
                            m = _re.search(r"/document/d/([^/]+)/", source_ref)
                            if m:
                                doc_id = m.group(1)
                                source_ref = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
                                logger.info(f"🔁 Converted Google Docs link to text export for {interview_id}")
                        try:
                            resp = requests.get(source_ref, timeout=20)
                            if resp.ok and resp.text and len(resp.text.strip()) > 50:
                                transcript = resp.text
                                logger.info(f"🌐 Fetched transcript from URL for {interview_id} ({len(transcript)} chars)")
                            else:
                                logger.warning(f"⚠️ Could not fetch usable transcript text from URL for {interview_id}: status={resp.status_code}")
                        except Exception as fetch_err:
                            logger.warning(f"⚠️ Fetch error for transcript URL in {interview_id}: {fetch_err}")
                    elif len(source_ref) < 260 and os.path.exists(source_ref):
                        try:
                            with open(source_ref, 'r', encoding='utf-8') as f:
                                transcript = f.read()
                            logger.info(f"📄 Loaded transcript from file for {interview_id} ({len(transcript)} chars)")
                        except Exception as file_err:
                            logger.warning(f"⚠️ Could not read transcript file for {interview_id}: {file_err}")
                     
            except Exception as e:
                logger.warning(f"⚠️ Error resolving transcript source for {interview_id}: {e}")
                # Guard: skip if still empty/very short
                if not isinstance(transcript, str) or len(transcript.strip()) < 5:
                    logger.warning(f"⚠️ Transcript empty or too short for {interview_id}; skipping extraction")
                    results.append({
                        'interview_id': interview_id,
                        'status': 'no_data',
                        'responses_extracted': 0,
                        'responses_saved': 0,
                        'interviewee': row['Interview Contact Full Name'],
                        'company': row['Interview Contact Company Name']
                    })
                    continue
            interviewee_name = row['Interview Contact Full Name']
            company = row['Interview Contact Company Name']
            deal_status = row['Deal Status']
            date_of_interview = row['Completion Date']
            industry = row['Industry']
            audio_video_link = row.get('Audio/Video Link', '')
            contact_website = row.get('Interview Contact Website', '')
            
            logger.info(f"📝 Processing interview {interview_id}: {interviewee_name} from {company}")
            
            # Ensure a minimal interview_metadata record exists for this interview
            try:
                self.db.upsert_interview_metadata(
                    client_id=client_id,
                    interview_id=interview_id,
                    interviewee_name=interviewee_name,
                    company=company,
                    deal_status=deal_status,
                    date_of_interview=str(date_of_interview)
                )
            except Exception as e:
                logger.warning(f"⚠️ Could not upsert interview_metadata for {interview_id}: {e}")

            try:
                # Create temporary file with transcript
                temp_file = f"temp_{interview_id}_{client_id}.txt"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(transcript)
                
                # Run Stage 1 extraction with specified processing mode
                if processing_mode == "parallel":
                    extracted_data = self.processor.stage1_core_extraction(
                        transcript_path=temp_file,
                        company=company,
                        interviewee=interviewee_name,
                        deal_status=deal_status,
                        date_of_interview=date_of_interview
                    )
                else:
                    # Use sequential processing
                    extracted_data = self.processor.stage1_core_extraction_sequential(
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
                        response['audio_video_link'] = audio_video_link
                        response['contact_website'] = contact_website
                    
                    # Harmonize subjects if harmonizer is available
                    if self.harmonizer:
                        harmonized_count = 0
                        for response in extracted_data:
                            try:
                                subject = response.get('subject', '')
                                verbatim_response = response.get('verbatim_response', '')
                                
                                if subject:
                                    harmonization_result = self.harmonizer.harmonize_subject(subject, verbatim_response)
                                    
                                    # Add harmonization data to response
                                    response['harmonized_subject'] = harmonization_result.get('harmonized_subject')
                                    response['harmonization_confidence'] = harmonization_result.get('confidence')
                                    response['harmonization_method'] = harmonization_result.get('mapping_method')
                                    response['harmonization_reasoning'] = harmonization_result.get('reasoning')
                                    response['suggested_new_category'] = harmonization_result.get('new_category_suggestion')
                                    response['harmonized_at'] = harmonization_result.get('mapped_at')
                                    
                                    harmonized_count += 1
                            except Exception as e:
                                logger.warning(f"⚠️ Failed to harmonize subject '{response.get('subject', '')}': {e}")
                                # Continue processing even if harmonization fails
                        
                        logger.info(f"✅ Auto-harmonized {harmonized_count}/{len(extracted_data)} responses from {interview_id}")
                    
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
                    
                    # Count harmonized responses for this interview
                    interview_harmonized = sum(1 for r in extracted_data if r.get('harmonized_subject'))
                    total_harmonized += interview_harmonized
                    
                    results.append({
                        'interview_id': interview_id,
                        'status': 'success',
                        'responses_extracted': len(extracted_data),
                        'responses_saved': success_count,
                        'responses_harmonized': interview_harmonized,
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
        logger.info(f"🎯 Total responses auto-harmonized: {total_harmonized}")
        
        if successful:
            avg_responses = sum(r['responses_extracted'] for r in successful) / len(successful)
            harmonization_rate = (total_harmonized / total_responses * 100) if total_responses > 0 else 0
            logger.info(f"📈 Average responses per interview: {avg_responses:.1f}")
            logger.info(f"🎯 Harmonization success rate: {harmonization_rate:.1f}%")
        
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
            'total_harmonized': total_harmonized,
            'harmonization_rate': (total_harmonized / total_responses * 100) if total_responses > 0 else 0,
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