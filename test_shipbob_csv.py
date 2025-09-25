"""
Test script specifically for ShipBob CSV format with enhanced timestamp parser
"""

import pandas as pd
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_timestamp_parser import EnhancedTimestampParser
from enhanced_database_save import create_timestamp_enhanced_response_data, format_timestamp_for_database
from supabase_database import SupabaseDatabase

def test_shipbob_csv_with_timestamps(csv_path, client_id="shipbob", max_rows=3, save_to_db=False):
    """Test timestamp extraction on ShipBob CSV file"""
    
    print("="*70)
    print("TESTING SHIPBOB CSV WITH ENHANCED TIMESTAMP EXTRACTION")
    print("="*70)
    
    # Load CSV
    print(f"\n1. Loading CSV: {csv_path}")
    try:
        df = pd.read_csv(csv_path)
        print(f"   ✅ Loaded {len(df)} rows")
        print(f"   📋 Columns: {list(df.columns)}")
    except Exception as e:
        print(f"   ❌ Error loading CSV: {e}")
        return
    
    # Check for required columns
    if 'Raw Transcript' not in df.columns:
        print("   ❌ CSV must contain 'Raw Transcript' column")
        return
    
    # Initialize enhanced parser
    parser = EnhancedTimestampParser()
    print("   ✅ Enhanced timestamp parser initialized")
    
    # Initialize database if needed
    db = None
    if save_to_db:
        try:
            db = SupabaseDatabase()
            print("   ✅ Database connected")
        except Exception as e:
            print(f"   ❌ Database connection failed: {e}")
            save_to_db = False
    
    # Process transcripts
    print(f"\n2. Processing first {max_rows} transcripts...")
    
    total_responses = 0
    total_with_timestamps = 0
    all_responses = []
    
    for index, row in df.head(max_rows).iterrows():
        print(f"\n   Processing row {index + 1}...")
        
        # Get transcript
        transcript = row.get('Raw Transcript', '')
        if not transcript or pd.isna(transcript):
            print(f"   ⚠️ Skipping: No transcript data")
            continue
        
        # Extract metadata from ShipBob CSV
        company = row.get('Interview Contact Company Name', f'Company_{index + 1}')
        interviewee = row.get('Interview Contact Full Name', f'Interviewee_{index + 1}')
        deal_status = row.get('Deal Status', 'closed_won')
        interview_date = row.get('Completion Date', datetime.now().strftime('%Y-%m-%d'))
        interview_id = row.get('Interview ID', f'IVW-{index + 1:05d}')
        
        print(f"   📊 Company: {company}")
        print(f"   👤 Interviewee: {interviewee}")
        print(f"   🆔 Interview ID: {interview_id}")
        print(f"   📝 Transcript length: {len(transcript)} characters")
        
        # Process transcript with enhanced parser
        responses = process_shipbob_transcript_with_timestamps(
            transcript, company, interviewee, deal_status, interview_date, client_id, interview_id, parser
        )
        
        if responses:
            print(f"   ✅ Extracted {len(responses)} responses")
            total_responses += len(responses)
            all_responses.extend(responses)
            
            # Count responses with timestamps
            timestamped_responses = [r for r in responses if r.get('start_timestamp') or r.get('end_timestamp')]
            total_with_timestamps += len(timestamped_responses)
            print(f"   🎬 {len(timestamped_responses)} responses have timestamps")
            
            # Show sample response
            if responses:
                sample = responses[0]
                print(f"   📝 Sample response:")
                print(f"      ID: {sample.get('response_id')}")
                print(f"      Subject: {sample.get('subject')}")
                print(f"      Start: {sample.get('start_timestamp', 'N/A')}")
                print(f"      End: {sample.get('end_timestamp', 'N/A')}")
                print(f"      Question: {sample.get('question', '')[:60]}...")
                print(f"      Response: {sample.get('verbatim_response', '')[:80]}...")
            
            # Save to database if requested
            if save_to_db and db:
                save_responses_to_database(db, responses)
                print(f"   💾 Saved to database")
        else:
            print(f"   ⚠️ No responses extracted")
    
    # Final results
    print(f"\n" + "="*70)
    print("PROCESSING COMPLETE")
    print("="*70)
    
    print(f"📊 Interviews processed: {max_rows}")
    print(f"📝 Total responses: {total_responses}")
    print(f"🎬 Responses with timestamps: {total_with_timestamps}")
    
    if total_responses > 0:
        timestamp_percentage = (total_with_timestamps / total_responses) * 100
        print(f"📈 Timestamp coverage: {timestamp_percentage:.1f}%")
    
    if save_to_db:
        print(f"💾 Data saved to database: {'Yes' if db else 'No'}")
    
    # Show all responses summary
    if all_responses:
        print(f"\n📋 All Responses Summary:")
        for i, response in enumerate(all_responses):
            print(f"   {i+1}. {response.get('response_id')} [{response.get('start_timestamp', 'N/A')}-{response.get('end_timestamp', 'N/A')}]")
            print(f"      {response.get('question', '')[:50]}...")
            print(f"      {response.get('verbatim_response', '')[:60]}...")
            print()

def process_shipbob_transcript_with_timestamps(transcript, company, interviewee, deal_status, interview_date, client_id, interview_id, parser):
    """Process a ShipBob transcript and extract responses with timestamps"""
    
    try:
        # Parse transcript into segments
        segments = parser.parse_transcript_segments(transcript)
        
        if not segments:
            return []
        
        # Find Q&A pairs
        qa_pairs = parser.find_qa_segments(segments)
        
        # Create responses from Q&A pairs
        responses = []
        for i, (question_seg, answer_seg) in enumerate(qa_pairs):
            response_id = f"{client_id}_{interview_id}_{i+1}"
            
            response = {
                "response_id": response_id,
                "verbatim_response": answer_seg.text,
                "subject": "Interview Response",
                "question": question_seg.text,
                "deal_status": deal_status,
                "company": company,
                "interviewee_name": interviewee,
                "interview_date": interview_date,
                "client_id": client_id,
                "interview_id": interview_id,
                "start_timestamp": answer_seg.start_timestamp,
                "end_timestamp": answer_seg.end_timestamp
            }
            
            # Format timestamps for database
            response['start_timestamp'] = format_timestamp_for_database(response['start_timestamp'])
            response['end_timestamp'] = format_timestamp_for_database(response['end_timestamp'])
            
            responses.append(response)
        
        return responses
        
    except Exception as e:
        print(f"   ❌ Error processing transcript: {e}")
        return []

def save_responses_to_database(db, responses):
    """Save responses to database"""
    for response in responses:
        try:
            db.save_core_response(response)
        except Exception as e:
            print(f"   ❌ Error saving response {response.get('response_id')}: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_shipbob_csv.py <csv_file> [client_id] [max_rows] [save_to_db]")
        print("Example: python test_shipbob_csv.py shipbob_data.csv shipbob 3 true")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    client_id = sys.argv[2] if len(sys.argv) > 2 else "shipbob"
    max_rows = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    save_to_db = sys.argv[4].lower() == 'true' if len(sys.argv) > 4 else False
    
    test_shipbob_csv_with_timestamps(csv_path, client_id, max_rows, save_to_db)
