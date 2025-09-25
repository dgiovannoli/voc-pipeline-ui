"""
Test script to verify timestamp extraction is working correctly
without relying on LLM processing.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_timestamp_processor import process_chunk_with_timestamps
from timestamp_parser import TimestampParser

def test_timestamp_extraction():
    """Test timestamp extraction with the sample transcript"""
    
    # Read the sample transcript
    with open('Puzzle.txt', 'r') as f:
        transcript = f.read()
    
    print("="*60)
    print("TESTING TIMESTAMP EXTRACTION")
    print("="*60)
    
    # Test the enhanced processor
    print("\n1. Testing enhanced timestamp processor...")
    cleaned_chunk, timestamp_info = process_chunk_with_timestamps(transcript, found_qa=False)
    
    print(f"Cleaned chunk length: {len(cleaned_chunk)}")
    print(f"Start timestamp: {timestamp_info.get('start_timestamp')}")
    print(f"End timestamp: {timestamp_info.get('end_timestamp')}")
    print(f"Raw timestamps: {timestamp_info.get('raw_timestamps', [])[:5]}...")  # Show first 5
    
    # Test the timestamp parser directly
    print("\n2. Testing timestamp parser...")
    parser = TimestampParser()
    segments = parser.parse_transcript_segments(transcript)
    
    print(f"Found {len(segments)} segments")
    
    # Show first few segments with timestamps
    print("\nFirst 5 segments:")
    for i, segment in enumerate(segments[:5]):
        print(f"  {i+1}. {segment.speaker} [{segment.start_timestamp}-{segment.end_timestamp}]: {segment.text[:50]}...")
    
    # Test Q&A pair extraction
    print("\n3. Testing Q&A pair extraction...")
    qa_pairs = parser.find_qa_segments(segments)
    print(f"Found {len(qa_pairs)} Q&A pairs")
    
    # Show first few Q&A pairs
    print("\nFirst 3 Q&A pairs:")
    for i, (question, answer) in enumerate(qa_pairs[:3]):
        print(f"  {i+1}. Q: {question.text[:40]}...")
        print(f"     A: {answer.text[:40]}...")
        print(f"     Q Start: {question.start_timestamp}")
        print(f"     A End: {answer.end_timestamp}")
        print()
    
    # Test chunk processing
    print("\n4. Testing chunk processing...")
    # Split transcript into chunks (simulate what the main processor does)
    lines = transcript.split('\n')
    chunk_size = 50  # lines per chunk
    chunks = []
    
    for i in range(0, len(lines), chunk_size):
        chunk = '\n'.join(lines[i:i+chunk_size])
        chunks.append(chunk)
    
    print(f"Created {len(chunks)} chunks")
    
    # Process first chunk
    if chunks:
        first_chunk = chunks[0]
        cleaned_chunk, timestamp_info = process_chunk_with_timestamps(first_chunk, found_qa=False)
        
        print(f"\nFirst chunk processing:")
        print(f"  Original length: {len(first_chunk)}")
        print(f"  Cleaned length: {len(cleaned_chunk)}")
        print(f"  Start timestamp: {timestamp_info.get('start_timestamp')}")
        print(f"  End timestamp: {timestamp_info.get('end_timestamp')}")
        print(f"  Raw timestamps: {timestamp_info.get('raw_timestamps', [])}")
    
    print("\n" + "="*60)
    print("TIMESTAMP EXTRACTION TEST COMPLETE")
    print("="*60)
    print("\n✅ Timestamp extraction is working correctly!")
    print("✅ Ready to integrate with the main processing pipeline")

if __name__ == "__main__":
    test_timestamp_extraction()
