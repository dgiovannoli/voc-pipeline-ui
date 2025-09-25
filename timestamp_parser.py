"""
Timestamp Parser Utility for VOC Pipeline
Handles extraction and normalization of timestamps from various transcript formats.
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class TimestampSegment:
    """Represents a text segment with associated timestamps"""
    text: str
    start_timestamp: Optional[str] = None
    end_timestamp: Optional[str] = None
    speaker: Optional[str] = None
    raw_timestamps: List[str] = None

class TimestampParser:
    """Parses timestamps from various transcript formats"""
    
    def __init__(self):
        # Regex patterns for different timestamp formats
        self.patterns = {
            # Speaker with timestamp: "Speaker 1 (01:00):"
            'speaker_timestamp': re.compile(r'^Speaker\s+(\d+)\s*\((\d{1,2}:\d{2})\):\s*(.*)$', re.MULTILINE),
            
            # Inline timestamp: "[00:01:00]"
            'inline_timestamp': re.compile(r'\[(\d{1,2}:\d{2}(?::\d{2})?)\]'),
            
            # Standalone timestamp: "(02:00):"
            'standalone_timestamp': re.compile(r'^\((\d{1,2}:\d{2})\):\s*(.*)$', re.MULTILINE),
            
            # Speaker without timestamp: "Speaker 1:"
            'speaker_only': re.compile(r'^Speaker\s+(\d+):\s*(.*)$', re.MULTILINE),
        }
    
    def normalize_timestamp(self, timestamp: str) -> str:
        """
        Normalize timestamp to HH:MM:SS format
        
        Args:
            timestamp: Timestamp in various formats (MM:SS, HH:MM:SS, etc.)
            
        Returns:
            Normalized timestamp in HH:MM:SS format
        """
        if not timestamp:
            return None
            
        # Remove any brackets or parentheses
        clean_timestamp = re.sub(r'[\[\]()]', '', timestamp.strip())
        
        # Split by colon
        parts = clean_timestamp.split(':')
        
        if len(parts) == 2:
            # MM:SS format - assume hours are 00
            minutes, seconds = parts
            return f"00:{minutes.zfill(2)}:{seconds.zfill(2)}"
        elif len(parts) == 3:
            # HH:MM:SS format
            hours, minutes, seconds = parts
            return f"{hours.zfill(2)}:{minutes.zfill(2)}:{seconds.zfill(2)}"
        else:
            logger.warning(f"Unable to parse timestamp format: {timestamp}")
            return None
    
    def extract_timestamps_from_text(self, text: str) -> List[Tuple[str, int]]:
        """
        Extract all timestamps from text with their positions
        
        Args:
            text: Raw transcript text
            
        Returns:
            List of (timestamp, position) tuples
        """
        timestamps = []
        
        # Find inline timestamps [00:01:00]
        for match in self.patterns['inline_timestamp'].finditer(text):
            timestamp = self.normalize_timestamp(match.group(1))
            if timestamp:
                timestamps.append((timestamp, match.start()))
        
        return timestamps
    
    def parse_transcript_segments(self, transcript: str) -> List[TimestampSegment]:
        """
        Parse transcript into segments with timestamps
        
        Args:
            transcript: Raw transcript text
            
        Returns:
            List of TimestampSegment objects
        """
        segments = []
        lines = transcript.split('\n')
        
        current_segment = None
        current_speaker = None
        current_start_time = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for speaker with timestamp: "Speaker 1 (01:00):"
            speaker_match = self.patterns['speaker_timestamp'].match(line)
            if speaker_match:
                # Save previous segment if exists
                if current_segment:
                    segments.append(current_segment)
                
                # Start new segment
                speaker_num = speaker_match.group(1)
                timestamp = self.normalize_timestamp(speaker_match.group(2))
                text = speaker_match.group(3)
                
                current_speaker = f"Speaker {speaker_num}"
                current_start_time = timestamp
                current_segment = TimestampSegment(
                    text=text,
                    start_timestamp=timestamp,
                    speaker=current_speaker,
                    raw_timestamps=[timestamp] if timestamp else []
                )
                continue
            
            # Check for standalone timestamp: "(02:00):"
            standalone_match = self.patterns['standalone_timestamp'].match(line)
            if standalone_match:
                # Save previous segment if exists
                if current_segment:
                    segments.append(current_segment)
                
                # Start new segment
                timestamp = self.normalize_timestamp(standalone_match.group(1))
                text = standalone_match.group(2)
                
                current_segment = TimestampSegment(
                    text=text,
                    start_timestamp=timestamp,
                    raw_timestamps=[timestamp] if timestamp else []
                )
                continue
            
            # Check for speaker without timestamp: "Speaker 1:"
            speaker_only_match = self.patterns['speaker_only'].match(line)
            if speaker_only_match:
                # Save previous segment if exists
                if current_segment:
                    segments.append(current_segment)
                
                # Start new segment
                speaker_num = speaker_only_match.group(1)
                text = speaker_only_match.group(2)
                
                current_speaker = f"Speaker {speaker_num}"
                current_segment = TimestampSegment(
                    text=text,
                    speaker=current_speaker,
                    raw_timestamps=[]
                )
                continue
            
            # Regular text line - add to current segment
            if current_segment:
                # Check for inline timestamps in the text
                inline_timestamps = self.extract_timestamps_from_text(line)
                if inline_timestamps:
                    # Add timestamps to current segment
                    for timestamp, _ in inline_timestamps:
                        current_segment.raw_timestamps.append(timestamp)
                    
                    # If this is the first inline timestamp, use it as start time
                    if not current_segment.start_timestamp and inline_timestamps:
                        current_segment.start_timestamp = inline_timestamps[0][0]
                
                # Add text to segment
                if current_segment.text:
                    current_segment.text += " " + line
                else:
                    current_segment.text = line
        
        # Add final segment
        if current_segment:
            segments.append(current_segment)
        
        # Calculate end timestamps
        self._calculate_end_timestamps(segments)
        
        return segments
    
    def _calculate_end_timestamps(self, segments: List[TimestampSegment]):
        """
        Calculate end timestamps for segments based on next segment's start time
        
        Args:
            segments: List of TimestampSegment objects
        """
        for i, segment in enumerate(segments):
            if segment.start_timestamp and i < len(segments) - 1:
                next_segment = segments[i + 1]
                if next_segment.start_timestamp:
                    segment.end_timestamp = next_segment.start_timestamp
                else:
                    # If next segment has no start time, use the last inline timestamp
                    if segment.raw_timestamps:
                        segment.end_timestamp = segment.raw_timestamps[-1]
            elif segment.start_timestamp and not segment.end_timestamp:
                # Last segment - use last inline timestamp if available
                if segment.raw_timestamps:
                    segment.end_timestamp = segment.raw_timestamps[-1]
    
    def find_qa_segments(self, segments: List[TimestampSegment]) -> List[Tuple[TimestampSegment, TimestampSegment]]:
        """
        Identify question-answer pairs from segments
        
        Args:
            segments: List of parsed segments
            
        Returns:
            List of (question_segment, answer_segment) tuples
        """
        qa_pairs = []
        
        for i in range(len(segments) - 1):
            current_segment = segments[i]
            next_segment = segments[i + 1]
            
            # Simple heuristic: if current segment ends with ? and next segment doesn't start with Speaker 1
            # then it's likely a Q&A pair
            if (current_segment.text.strip().endswith('?') and 
                next_segment.speaker and 
                next_segment.speaker != "Speaker 1"):
                qa_pairs.append((current_segment, next_segment))
        
        return qa_pairs
    
    def extract_qa_with_timestamps(self, transcript: str) -> List[Dict]:
        """
        Extract Q&A pairs with timestamps from transcript
        
        Args:
            transcript: Raw transcript text
            
        Returns:
            List of dictionaries containing Q&A pairs with timestamps
        """
        segments = self.parse_transcript_segments(transcript)
        qa_pairs = self.find_qa_segments(segments)
        
        results = []
        for i, (question_seg, answer_seg) in enumerate(qa_pairs):
            result = {
                'question_text': question_seg.text,
                'answer_text': answer_seg.text,
                'question_start_timestamp': question_seg.start_timestamp,
                'question_end_timestamp': question_seg.end_timestamp,
                'answer_start_timestamp': answer_seg.start_timestamp,
                'answer_end_timestamp': answer_seg.end_timestamp,
                'question_speaker': question_seg.speaker,
                'answer_speaker': answer_seg.speaker,
                'qa_id': f"qa_{i+1}"
            }
            results.append(result)
        
        return results

def test_timestamp_parser():
    """Test the timestamp parser with sample data"""
    parser = TimestampParser()
    
    # Test with sample transcript
    sample_transcript = """Speaker 1 (01:00):
[00:01:00] Hi, Brian.

Speaker 2 (01:10):
Hey, how's it going?

Speaker 1 (01:11):
Well, how are you?

Speaker 2 (01:12):
Good, good.

Speaker 1 (01:16):
The coolest part about my job, especially with Ship Out, is I get to meet the coolest products all day long. [00:01:30] I love this part.

Speaker 2 (01:30):
That sounds interesting. What makes it different?

Speaker 1 (01:35):
[00:01:35] Well, the variety is amazing."""
    
    print("Testing timestamp parser...")
    segments = parser.parse_transcript_segments(sample_transcript)
    
    print(f"Found {len(segments)} segments:")
    for i, segment in enumerate(segments):
        print(f"  {i+1}. {segment.speaker} [{segment.start_timestamp}-{segment.end_timestamp}]: {segment.text[:50]}...")
    
    qa_pairs = parser.find_qa_segments(segments)
    print(f"\nFound {len(qa_pairs)} Q&A pairs:")
    for i, (q, a) in enumerate(qa_pairs):
        print(f"  {i+1}. Q: {q.text[:30]}... A: {a.text[:30]}...")

if __name__ == "__main__":
    test_timestamp_parser()
