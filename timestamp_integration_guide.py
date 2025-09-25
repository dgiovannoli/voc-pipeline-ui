"""
Timestamp Integration Guide for VOC Pipeline
Demonstrates how to integrate timestamp support into the existing stage 1 processing.
"""

import json
import os
from typing import List, Dict
from enhanced_timestamp_processor import process_chunk_with_timestamps
from enhanced_stage1_processor import process_chunk_with_timestamp_support
from timestamp_parser import TimestampParser

def demonstrate_timestamp_extraction():
    """Demonstrate timestamp extraction from the sample transcript"""
    
    # Read the sample transcript
    with open('Puzzle.txt', 'r') as f:
        transcript = f.read()
    
    print("="*60)
    print("TIMESTAMP EXTRACTION DEMONSTRATION")
    print("="*60)
    
    # Parse the transcript into segments
    parser = TimestampParser()
    segments = parser.parse_transcript_segments(transcript)
    
    print(f"Found {len(segments)} segments with timestamps:")
    print()
    
    for i, segment in enumerate(segments[:10]):  # Show first 10 segments
        print(f"Segment {i+1}:")
        print(f"  Speaker: {segment.speaker}")
        print(f"  Start: {segment.start_timestamp}")
        print(f"  End: {segment.end_timestamp}")
        print(f"  Text: {segment.text[:100]}...")
        print()
    
    # Find Q&A pairs
    qa_pairs = parser.find_qa_segments(segments)
    print(f"Found {len(qa_pairs)} Q&A pairs:")
    print()
    
    for i, (question, answer) in enumerate(qa_pairs[:5]):  # Show first 5 Q&A pairs
        print(f"Q&A Pair {i+1}:")
        print(f"  Question: {question.text[:80]}...")
        print(f"  Answer: {answer.text[:80]}...")
        print(f"  Q Start: {question.start_timestamp}")
        print(f"  A End: {answer.end_timestamp}")
        print()

def demonstrate_enhanced_processing():
    """Demonstrate enhanced processing with timestamps"""
    
    print("="*60)
    print("ENHANCED PROCESSING DEMONSTRATION")
    print("="*60)
    
    # Sample chunk from the transcript
    sample_chunk = """Speaker 1 (01:00):
[00:01:00] Hi, Brian. What was your current solution at the time?

Speaker 2 (01:10):
[00:01:10] We had our own warehouse, own software, own negotiated rates.

Speaker 1 (01:15):
[00:01:15] And what prompted you to consider options outside of that?

Speaker 2 (01:20):
[00:01:20] We're at the point where I either need to open up other warehouses or find someone that has a three PL network that I can rent little spaces from to take advantage of economies of scale at shipping."""
    
    # Process with timestamp support
    cleaned_chunk, timestamp_info = process_chunk_with_timestamps(sample_chunk, found_qa=False)
    
    print("Original chunk:")
    print(sample_chunk)
    print()
    
    print("Cleaned chunk:")
    print(cleaned_chunk)
    print()
    
    print("Timestamp information:")
    print(f"  Start: {timestamp_info.get('start_timestamp')}")
    print(f"  End: {timestamp_info.get('end_timestamp')}")
    print(f"  Raw timestamps: {timestamp_info.get('raw_timestamps')}")
    print()

def demonstrate_database_integration():
    """Demonstrate how timestamps would be stored in the database"""
    
    print("="*60)
    print("DATABASE INTEGRATION DEMONSTRATION")
    print("="*60)
    
    # Sample response data with timestamps
    sample_response = {
        "response_id": "shipbob_puzzle_brian_1",
        "verbatim_response": "We had our own warehouse, own software, own negotiated rates.",
        "subject": "Current Solution",
        "question": "What was your current solution at the time?",
        "start_timestamp": "00:01:10",
        "end_timestamp": "00:01:15",
        "deal_status": "closed_won",
        "company": "Puzzle",
        "interviewee_name": "Brian",
        "date_of_interview": "2024-01-01",
        "client_id": "shipbob"
    }
    
    print("Sample response data for database storage:")
    print(json.dumps(sample_response, indent=2))
    print()
    
    print("Database fields that would be populated:")
    print("  - response_id: Unique identifier")
    print("  - verbatim_response: The actual quote")
    print("  - subject: Topic category")
    print("  - question: The question that elicited this response")
    print("  - start_timestamp: When the response begins (HH:MM:SS)")
    print("  - end_timestamp: When the response ends (HH:MM:SS)")
    print("  - deal_status: Win/loss status")
    print("  - company: Company name")
    print("  - interviewee_name: Person interviewed")
    print("  - date_of_interview: Interview date")
    print("  - client_id: Client identifier")
    print()

def demonstrate_video_integration():
    """Demonstrate how timestamps enable video integration"""
    
    print("="*60)
    print("VIDEO INTEGRATION DEMONSTRATION")
    print("="*60)
    
    # Sample responses with timestamps
    responses = [
        {
            "response_id": "shipbob_puzzle_brian_1",
            "verbatim_response": "We had our own warehouse, own software, own negotiated rates.",
            "start_timestamp": "00:01:10",
            "end_timestamp": "00:01:15"
        },
        {
            "response_id": "shipbob_puzzle_brian_2", 
            "verbatim_response": "We're at the point where I either need to open up other warehouses or find someone that has a three PL network.",
            "start_timestamp": "00:01:20",
            "end_timestamp": "00:01:45"
        }
    ]
    
    print("Video integration capabilities:")
    print()
    
    for response in responses:
        print(f"Response: {response['response_id']}")
        print(f"  Quote: {response['verbatim_response'][:60]}...")
        print(f"  Video start: {response['start_timestamp']}")
        print(f"  Video end: {response['end_timestamp']}")
        print(f"  Duration: {calculate_duration(response['start_timestamp'], response['end_timestamp'])} seconds")
        print()
    
    print("Benefits:")
    print("  ✅ Precise video navigation to specific quotes")
    print("  ✅ Automatic video segment extraction")
    print("  ✅ Timeline-based quote organization")
    print("  ✅ Enhanced user experience for quote review")
    print()

def calculate_duration(start_time: str, end_time: str) -> int:
    """Calculate duration in seconds between two timestamps"""
    def time_to_seconds(time_str: str) -> int:
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
    return end_seconds - start_seconds

def main():
    """Run all demonstrations"""
    print("VOC Pipeline Timestamp Integration Guide")
    print("="*60)
    print()
    
    # Check if sample transcript exists
    if not os.path.exists('Puzzle.txt'):
        print("❌ Sample transcript 'Puzzle.txt' not found. Please ensure it's in the current directory.")
        return
    
    try:
        demonstrate_timestamp_extraction()
        demonstrate_enhanced_processing()
        demonstrate_database_integration()
        demonstrate_video_integration()
        
        print("="*60)
        print("INTEGRATION COMPLETE")
        print("="*60)
        print()
        print("Next steps:")
        print("1. Update your database schema to include start_timestamp and end_timestamp columns")
        print("2. Modify your stage 1 processing pipeline to use the enhanced functions")
        print("3. Update your database save functions to include timestamp fields")
        print("4. Test with your actual transcript data")
        print("5. Implement video integration using the timestamp data")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
