"""
Enhanced Timestamp Parser for ShipBob CSV Format
Handles the specific timestamp format used in your CSV files.
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

class EnhancedTimestampParser:
    """Enhanced parser that handles ShipBob CSV timestamp format"""
    
    def __init__(self):
        # Regex patterns for ShipBob format: "Speaker Name (00:00:38 - 00:00:39)"
        self.patterns = {
            'speaker_with_timestamps': re.compile(r'^([^(]+)\s*\((\d{2}:\d{2}:\d{2})\s*-\s*(\d{2}:\d{2}:\d{2})\)\s*(.*)$', re.MULTILINE),
            'speaker_with_single_timestamp': re.compile(r'^([^(]+)\s*\((\d{2}:\d{2}:\d{2})\)\s*(.*)$', re.MULTILINE),
            # Also handle the original formats
            'speaker_timestamp': re.compile(r'^Speaker\s+(\d+)\s*\((\d{1,2}:\d{2})\):\s*(.*)$', re.MULTILINE),
            'inline_timestamp': re.compile(r'\[(\d{1,2}:\d{2}(?::\d{2})?)\]'),
            'standalone_timestamp': re.compile(r'^\((\d{1,2}:\d{2})\):\s*(.*)$', re.MULTILINE),
        }
    
    def normalize_timestamp(self, timestamp: str) -> str:
        """Normalize timestamp to HH:MM:SS format"""
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
    
    def parse_transcript_segments(self, transcript: str) -> List[TimestampSegment]:
        """Parse transcript into segments with timestamps for ShipBob format"""
        segments = []
        lines = transcript.split('\n')
        
        current_segment = None
        current_speaker = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for ShipBob format: "Speaker Name (00:00:38 - 00:00:39)"
            shipbob_match = self.patterns['speaker_with_timestamps'].match(line)
            if shipbob_match:
                # Save previous segment if exists
                if current_segment:
                    segments.append(current_segment)
                
                # Start new segment
                speaker_name = shipbob_match.group(1).strip()
                start_timestamp = self.normalize_timestamp(shipbob_match.group(2))
                end_timestamp = self.normalize_timestamp(shipbob_match.group(3))
                text = shipbob_match.group(4).strip()
                
                current_speaker = speaker_name
                current_segment = TimestampSegment(
                    text=text,
                    start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp,
                    speaker=current_speaker,
                    raw_timestamps=[start_timestamp, end_timestamp] if start_timestamp and end_timestamp else []
                )
                continue
            
            # Check for single timestamp format: "Speaker Name (00:00:38)"
            single_timestamp_match = self.patterns['speaker_with_single_timestamp'].match(line)
            if single_timestamp_match:
                # Save previous segment if exists
                if current_segment:
                    segments.append(current_segment)
                
                # Start new segment
                speaker_name = single_timestamp_match.group(1).strip()
                timestamp = self.normalize_timestamp(single_timestamp_match.group(2))
                text = single_timestamp_match.group(3).strip()
                
                current_speaker = speaker_name
                current_segment = TimestampSegment(
                    text=text,
                    start_timestamp=timestamp,
                    speaker=current_speaker,
                    raw_timestamps=[timestamp] if timestamp else []
                )
                continue
            
            # Check for original formats
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
                current_segment = TimestampSegment(
                    text=text,
                    start_timestamp=timestamp,
                    speaker=current_speaker,
                    raw_timestamps=[timestamp] if timestamp else []
                )
                continue
            
            # Regular text line - add to current segment
            if current_segment:
                # Check for inline timestamps in the text
                inline_timestamps = self.extract_timestamps_from_text(line)
                if inline_timestamps:
                    for timestamp, _ in inline_timestamps:
                        current_segment.raw_timestamps.append(timestamp)
                
                # Add text to segment
                if current_segment.text:
                    current_segment.text += " " + line
                else:
                    current_segment.text = line
        
        # Add final segment
        if current_segment:
            segments.append(current_segment)
        
        # Calculate end timestamps for segments that don't have them
        self._calculate_end_timestamps(segments)
        
        return segments
    
    def extract_timestamps_from_text(self, text: str) -> List[Tuple[str, int]]:
        """Extract all timestamps from text with their positions"""
        timestamps = []
        
        # Find inline timestamps [00:01:00]
        for match in self.patterns['inline_timestamp'].finditer(text):
            timestamp = self.normalize_timestamp(match.group(1))
            if timestamp:
                timestamps.append((timestamp, match.start()))
        
        return timestamps
    
    def _calculate_end_timestamps(self, segments: List[TimestampSegment]):
        """Calculate end timestamps for segments based on next segment's start time"""
        for i, segment in enumerate(segments):
            if segment.start_timestamp and not segment.end_timestamp and i < len(segments) - 1:
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
        """Identify question-answer pairs from segments"""
        qa_pairs = []
        
        for i in range(len(segments) - 1):
            current_segment = segments[i]
            next_segment = segments[i + 1]
            
            # Look for Q&A patterns
            # Question: usually ends with ? or contains question words
            # Answer: usually the next segment from a different speaker
            is_question = (
                current_segment.text.strip().endswith('?') or
                any(word in current_segment.text.lower() for word in ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'can you', 'could you', 'would you'])
            )
            
            is_answer = (
                next_segment.speaker and 
                next_segment.speaker != current_segment.speaker and
                len(next_segment.text.strip()) > 10  # Substantial response
            )
            
            if is_question and is_answer:
                qa_pairs.append((current_segment, next_segment))
        
        return qa_pairs
    
    def extract_qa_with_timestamps(self, transcript: str) -> List[Dict]:
        """Extract Q&A pairs with timestamps from transcript"""
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

def test_enhanced_parser():
    """Test the enhanced parser with ShipBob format"""
    parser = EnhancedTimestampParser()
    
    # Test with ShipBob format
    sample_transcript = """Metro Vein Centers
Speaker 1 Drew Giovannoli
Speaker 2 Nick Codispoti

Nick Codispoti (00:00:38 - 00:00:39)
Adri, nice to meet you.

Drew Giovannoli (00:00:40 - 00:00:43)
Hey, Nick, nice to meet you as well. Thanks for taking time. Of course.

Nick Codispoti (00:00:44 - 00:00:45)
How can I help?

Drew Giovannoli (00:00:47 - 00:01:16)
I conduct research. My agency does market research for companies like ShipBob."""
    
    print("Testing enhanced timestamp parser...")
    segments = parser.parse_transcript_segments(sample_transcript)
    
    print(f"Found {len(segments)} segments:")
    for i, segment in enumerate(segments):
        print(f"  {i+1}. {segment.speaker} [{segment.start_timestamp}-{segment.end_timestamp}]: {segment.text[:50]}...")
    
    qa_pairs = parser.find_qa_segments(segments)
    print(f"\nFound {len(qa_pairs)} Q&A pairs:")
    for i, (q, a) in enumerate(qa_pairs):
        print(f"  {i+1}. Q: {q.text[:30]}... A: {a.text[:30]}...")

if __name__ == "__main__":
    test_enhanced_parser()
