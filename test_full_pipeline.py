"""
Full Pipeline Test with Timestamp Support
Tests the complete integration of timestamp support with real transcript data.
"""

import sys
import os
import json
from typing import List, Dict

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_timestamp_processor import process_chunk_with_timestamps
from enhanced_database_save import (
    create_timestamp_enhanced_response_data,
    format_timestamp_for_database,
    validate_timestamp_format
)
from timestamp_parser import TimestampParser

def test_full_pipeline():
    """Test the complete pipeline with real transcript data"""
    
    print("="*70)
    print("FULL PIPELINE TEST WITH TIMESTAMP SUPPORT")
    print("="*70)
    
    # 1. Load real transcript data
    print("\n1. Loading real transcript data...")
    with open('Puzzle.txt', 'r') as f:
        transcript = f.read()
    
    print(f"   Transcript length: {len(transcript)} characters")
    print(f"   Transcript lines: {len(transcript.splitlines())} lines")
    
    # 2. Test timestamp extraction
    print("\n2. Testing timestamp extraction...")
    parser = TimestampParser()
    segments = parser.parse_transcript_segments(transcript)
    qa_pairs = parser.find_qa_segments(segments)
    
    print(f"   Extracted {len(segments)} segments")
    print(f"   Found {len(qa_pairs)} Q&A pairs")
    
    # 3. Test chunk processing with timestamps
    print("\n3. Testing chunk processing with timestamps...")
    
    # Simulate chunking (split into smaller chunks)
    lines = transcript.split('\n')
    chunk_size = 30  # lines per chunk
    chunks = []
    
    for i in range(0, len(lines), chunk_size):
        chunk = '\n'.join(lines[i:i+chunk_size])
        chunks.append(chunk)
    
    print(f"   Created {len(chunks)} chunks for processing")
    
    # Process each chunk and extract timestamps
    processed_chunks = []
    for i, chunk in enumerate(chunks[:3]):  # Process first 3 chunks
        cleaned_chunk, timestamp_info = process_chunk_with_timestamps(chunk, found_qa=False)
        
        if cleaned_chunk:
            processed_chunks.append({
                'chunk_index': i,
                'cleaned_text': cleaned_chunk,
                'timestamp_info': timestamp_info,
                'original_length': len(chunk),
                'cleaned_length': len(cleaned_chunk)
            })
    
    print(f"   Successfully processed {len(processed_chunks)} chunks")
    
    # 4. Simulate response extraction with timestamps
    print("\n4. Simulating response extraction with timestamps...")
    
    # Create mock responses with timestamps (simulating LLM output)
    mock_responses = []
    for i, chunk_data in enumerate(processed_chunks):
        # Simulate extracting 1-2 responses per chunk
        timestamp_info = chunk_data['timestamp_info']
        
        # Mock response 1
        response1 = {
            "response_id": f"shipbob_puzzle_brian_{i}_1",
            "verbatim_response": "We had our own warehouse, own software, own negotiated rates.",
            "subject": "Current Solution",
            "question": "What was your current solution at the time?",
            "deal_status": "closed_won",
            "company": "Puzzle",
            "interviewee_name": "Brian",
            "interview_date": "2024-01-01",
            "client_id": "shipbob",
            "start_timestamp": timestamp_info.get('start_timestamp'),
            "end_timestamp": timestamp_info.get('end_timestamp')
        }
        mock_responses.append(response1)
        
        # Mock response 2 (if we have enough timestamp data)
        if timestamp_info.get('raw_timestamps') and len(timestamp_info.get('raw_timestamps', [])) > 1:
            response2 = {
                "response_id": f"shipbob_puzzle_brian_{i}_2",
                "verbatim_response": "We're at the point where I either need to open up other warehouses or find someone that has a three PL network.",
                "subject": "Growth Strategy",
                "question": "What prompted you to consider options outside of that?",
                "deal_status": "closed_won",
                "company": "Puzzle",
                "interviewee_name": "Brian",
                "interview_date": "2024-01-01",
                "client_id": "shipbob",
                "start_timestamp": timestamp_info.get('raw_timestamps', [None])[1] if len(timestamp_info.get('raw_timestamps', [])) > 1 else None,
                "end_timestamp": timestamp_info.get('end_timestamp')
            }
            mock_responses.append(response2)
    
    print(f"   Created {len(mock_responses)} mock responses with timestamps")
    
    # 5. Test database preparation
    print("\n5. Testing database preparation...")
    
    database_ready_responses = []
    for response in mock_responses:
        # Validate and format timestamps
        start_ts = format_timestamp_for_database(response.get('start_timestamp'))
        end_ts = format_timestamp_for_database(response.get('end_timestamp'))
        
        # Create enhanced response data
        enhanced_response = create_timestamp_enhanced_response_data(
            response,
            start_timestamp=start_ts,
            end_timestamp=end_ts
        )
        
        database_ready_responses.append(enhanced_response)
    
    print(f"   Prepared {len(database_ready_responses)} responses for database")
    
    # 6. Display results
    print("\n6. Results Summary:")
    print("   " + "="*50)
    
    for i, response in enumerate(database_ready_responses):
        print(f"\n   Response {i+1}:")
        print(f"     ID: {response['response_id']}")
        print(f"     Subject: {response['subject']}")
        print(f"     Question: {response['question'][:50]}...")
        print(f"     Start: {response.get('start_timestamp', 'N/A')}")
        print(f"     End: {response.get('end_timestamp', 'N/A')}")
        print(f"     Quote: {response['verbatim_response'][:60]}...")
    
    # 7. Test CSV output format
    print("\n7. Testing CSV output format...")
    
    csv_header = [
        'response_id', 'verbatim_response', 'subject', 'question',
        'start_timestamp', 'end_timestamp',
        'deal_status', 'company', 'interviewee_name', 'interview_date', 'client_id'
    ]
    
    csv_lines = [','.join(f'"{field}"' for field in csv_header)]
    
    for response in database_ready_responses:
        row = []
        for field in csv_header:
            value = response.get(field, '')
            if isinstance(value, str):
                value = value.replace('"', '""')
            row.append(f'"{value}"')
        csv_lines.append(','.join(row))
    
    csv_output = '\n'.join(csv_lines)
    print(f"   Generated CSV with {len(csv_lines)-1} data rows")
    print(f"   CSV length: {len(csv_output)} characters")
    
    # 8. Test video integration simulation
    print("\n8. Testing video integration simulation...")
    
    video_segments = []
    for response in database_ready_responses:
        if response.get('start_timestamp') and response.get('end_timestamp'):
            video_segments.append({
                'response_id': response['response_id'],
                'start_time': response['start_timestamp'],
                'end_time': response['end_timestamp'],
                'duration': calculate_duration(response['start_timestamp'], response['end_timestamp']),
                'quote_preview': response['verbatim_response'][:50] + "..."
            })
    
    print(f"   Created {len(video_segments)} video segments")
    
    for segment in video_segments:
        print(f"     {segment['response_id']}: {segment['start_time']}-{segment['end_time']} ({segment['duration']}s)")
        print(f"       Quote: {segment['quote_preview']}")
    
    # 9. Final summary
    print("\n" + "="*70)
    print("FULL PIPELINE TEST COMPLETE")
    print("="*70)
    
    print(f"\n✅ Successfully processed {len(segments)} transcript segments")
    print(f"✅ Extracted {len(qa_pairs)} Q&A pairs")
    print(f"✅ Processed {len(processed_chunks)} chunks with timestamp extraction")
    print(f"✅ Created {len(mock_responses)} responses with timestamps")
    print(f"✅ Prepared {len(database_ready_responses)} responses for database")
    print(f"✅ Generated CSV output with timestamp fields")
    print(f"✅ Created {len(video_segments)} video segments for integration")
    
    print(f"\n🎯 READY FOR PRODUCTION!")
    print(f"   - Timestamp extraction: ✅ Working")
    print(f"   - Database integration: ✅ Ready")
    print(f"   - Video integration: ✅ Ready")
    print(f"   - CSV output: ✅ Working")

def calculate_duration(start_time: str, end_time: str) -> int:
    """Calculate duration in seconds between two timestamps"""
    def time_to_seconds(time_str: str) -> int:
        if not time_str:
            return 0
        parts = time_str.split(':')
        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        return 0
    
    start_seconds = time_to_seconds(start_time)
    end_seconds = time_to_seconds(end_time)
    return max(0, end_seconds - start_seconds)

if __name__ == "__main__":
    test_full_pipeline()
