"""
Universal Timestamp Processor
Future-proof solution that can handle any interview format with timestamps.
"""

import pandas as pd
import sys
import os
import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_database_save import create_timestamp_enhanced_response_data, format_timestamp_for_database
from supabase_database import SupabaseDatabase

logger = logging.getLogger(__name__)

@dataclass
class TimestampSegment:
    """Represents a text segment with associated timestamps"""
    text: str
    start_timestamp: Optional[str] = None
    end_timestamp: Optional[str] = None
    speaker: Optional[str] = None
    raw_timestamps: List[str] = None

class UniversalTimestampParser:
    """Universal parser that can handle any timestamp format"""
    
    def __init__(self):
        # Comprehensive regex patterns for different timestamp formats
        self.patterns = {
            # ShipBob format: "Speaker Name (00:00:38 - 00:00:39)"
            'shipbob_format': re.compile(r'^([^(]+)\s*\((\d{2}:\d{2}:\d{2})\s*-\s*(\d{2}:\d{2}:\d{2})\)\s*(.*)$', re.MULTILINE),
            
            # Single timestamp format: "Speaker Name (00:00:38)"
            'single_timestamp': re.compile(r'^([^(]+)\s*\((\d{2}:\d{2}:\d{2})\)\s*(.*)$', re.MULTILINE),
            
            # Original format: "Speaker 1 (01:00):"
            'speaker_timestamp': re.compile(r'^Speaker\s+(\d+)\s*\((\d{1,2}:\d{2})\):\s*(.*)$', re.MULTILINE),
            
            # Inline timestamp: "[00:01:00]"
            'inline_timestamp': re.compile(r'\[(\d{1,2}:\d{2}(?::\d{2})?)\]'),
            
            # Standalone timestamp: "(02:00):"
            'standalone_timestamp': re.compile(r'^\((\d{1,2}:\d{2})\):\s*(.*)$', re.MULTILINE),
            
            # Rev format: "Speaker 1 (01:00:00):"
            'rev_format': re.compile(r'^Speaker\s+(\d+)\s*\((\d{2}:\d{2}:\d{2})\):\s*(.*)$', re.MULTILINE),
            
            # Generic format: "Name (HH:MM:SS):"
            'generic_format': re.compile(r'^([^(]+)\s*\((\d{2}:\d{2}:\d{2})\):\s*(.*)$', re.MULTILINE),
        }
    
    def detect_format(self, transcript: str) -> str:
        """Detect the timestamp format used in the transcript"""
        
        # Sample first 1000 characters for format detection
        sample = transcript[:1000]
        
        # Check for ShipBob format
        if self.patterns['shipbob_format'].search(sample):
            return 'shipbob'
        
        # Check for Rev format
        if self.patterns['rev_format'].search(sample):
            return 'rev'
        
        # Check for original format
        if self.patterns['speaker_timestamp'].search(sample):
            return 'original'
        
        # Check for generic format
        if self.patterns['generic_format'].search(sample):
            return 'generic'
        
        # Check for inline timestamps
        if self.patterns['inline_timestamp'].search(sample):
            return 'inline'
        
        return 'unknown'
    
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
        """Parse transcript into segments with timestamps using detected format"""
        
        format_type = self.detect_format(transcript)
        logger.info(f"Detected format: {format_type}")
        
        if format_type == 'shipbob':
            return self._parse_shipbob_format(transcript)
        elif format_type == 'rev':
            return self._parse_rev_format(transcript)
        elif format_type == 'original':
            return self._parse_original_format(transcript)
        elif format_type == 'generic':
            return self._parse_generic_format(transcript)
        elif format_type == 'inline':
            return self._parse_inline_format(transcript)
        else:
            logger.warning(f"Unknown format, attempting generic parsing")
            return self._parse_generic_format(transcript)
    
    def _parse_shipbob_format(self, transcript: str) -> List[TimestampSegment]:
        """Parse ShipBob format: Speaker Name (00:00:38 - 00:00:39)"""
        segments = []
        lines = transcript.split('\n')
        
        current_segment = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for ShipBob format
            match = self.patterns['shipbob_format'].match(line)
            if match:
                if current_segment:
                    segments.append(current_segment)
                
                speaker_name = match.group(1).strip()
                start_timestamp = self.normalize_timestamp(match.group(2))
                end_timestamp = self.normalize_timestamp(match.group(3))
                text = match.group(4).strip()
                
                current_segment = TimestampSegment(
                    text=text,
                    start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp,
                    speaker=speaker_name,
                    raw_timestamps=[start_timestamp, end_timestamp] if start_timestamp and end_timestamp else []
                )
                continue
            
            # Regular text line
            if current_segment:
                if current_segment.text:
                    current_segment.text += " " + line
                else:
                    current_segment.text = line
        
        if current_segment:
            segments.append(current_segment)
        
        return segments
    
    def _parse_rev_format(self, transcript: str) -> List[TimestampSegment]:
        """Parse Rev format: Speaker 1 (01:00:00):"""
        segments = []
        lines = transcript.split('\n')
        
        current_segment = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            match = self.patterns['rev_format'].match(line)
            if match:
                if current_segment:
                    segments.append(current_segment)
                
                speaker_num = match.group(1)
                timestamp = self.normalize_timestamp(match.group(2))
                text = match.group(3)
                
                current_segment = TimestampSegment(
                    text=text,
                    start_timestamp=timestamp,
                    speaker=f"Speaker {speaker_num}",
                    raw_timestamps=[timestamp] if timestamp else []
                )
                continue
            
            if current_segment:
                if current_segment.text:
                    current_segment.text += " " + line
                else:
                    current_segment.text = line
        
        if current_segment:
            segments.append(current_segment)
        
        self._calculate_end_timestamps(segments)
        return segments
    
    def _parse_original_format(self, transcript: str) -> List[TimestampSegment]:
        """Parse original format: Speaker 1 (01:00):"""
        segments = []
        lines = transcript.split('\n')
        
        current_segment = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            match = self.patterns['speaker_timestamp'].match(line)
            if match:
                if current_segment:
                    segments.append(current_segment)
                
                speaker_num = match.group(1)
                timestamp = self.normalize_timestamp(match.group(2))
                text = match.group(3)
                
                current_segment = TimestampSegment(
                    text=text,
                    start_timestamp=timestamp,
                    speaker=f"Speaker {speaker_num}",
                    raw_timestamps=[timestamp] if timestamp else []
                )
                continue
            
            if current_segment:
                if current_segment.text:
                    current_segment.text += " " + line
                else:
                    current_segment.text = line
        
        if current_segment:
            segments.append(current_segment)
        
        self._calculate_end_timestamps(segments)
        return segments
    
    def _parse_generic_format(self, transcript: str) -> List[TimestampSegment]:
        """Parse generic format: Name (HH:MM:SS):"""
        segments = []
        lines = transcript.split('\n')
        
        current_segment = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            match = self.patterns['generic_format'].match(line)
            if match:
                if current_segment:
                    segments.append(current_segment)
                
                speaker_name = match.group(1).strip()
                timestamp = self.normalize_timestamp(match.group(2))
                text = match.group(3)
                
                current_segment = TimestampSegment(
                    text=text,
                    start_timestamp=timestamp,
                    speaker=speaker_name,
                    raw_timestamps=[timestamp] if timestamp else []
                )
                continue
            
            if current_segment:
                if current_segment.text:
                    current_segment.text += " " + line
                else:
                    current_segment.text = line
        
        if current_segment:
            segments.append(current_segment)
        
        self._calculate_end_timestamps(segments)
        return segments
    
    def _parse_inline_format(self, transcript: str) -> List[TimestampSegment]:
        """Parse inline format with [00:01:00] timestamps"""
        # This would be more complex - for now, return empty
        return []
    
    def _calculate_end_timestamps(self, segments: List[TimestampSegment]):
        """Calculate end timestamps for segments"""
        for i, segment in enumerate(segments):
            if segment.start_timestamp and not segment.end_timestamp and i < len(segments) - 1:
                next_segment = segments[i + 1]
                if next_segment.start_timestamp:
                    segment.end_timestamp = next_segment.start_timestamp
    
    def find_qa_segments(self, segments: List[TimestampSegment]) -> List[Tuple[TimestampSegment, TimestampSegment]]:
        """Identify question-answer pairs from segments"""
        qa_pairs = []
        
        for i in range(len(segments) - 1):
            current_segment = segments[i]
            next_segment = segments[i + 1]
            
            # Look for Q&A patterns
            is_question = (
                current_segment.text.strip().endswith('?') or
                any(word in current_segment.text.lower() for word in ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'can you', 'could you', 'would you'])
            )
            
            is_answer = (
                next_segment.speaker and 
                next_segment.speaker != current_segment.speaker and
                len(next_segment.text.strip()) > 10
            )
            
            if is_question and is_answer:
                qa_pairs.append((current_segment, next_segment))
        
        return qa_pairs

def process_universal_transcript_with_timestamps(transcript, company, interviewee, deal_status, interview_date, client_id, interview_id=None):
    """Process any transcript format and extract responses with timestamps"""
    
    try:
        # Initialize universal parser
        parser = UniversalTimestampParser()
        
        # Parse transcript into segments
        segments = parser.parse_transcript_segments(transcript)
        
        if not segments:
            return []
        
        # Find Q&A pairs
        qa_pairs = parser.find_qa_segments(segments)
        
        # Create responses from Q&A pairs
        responses = []
        for i, (question_seg, answer_seg) in enumerate(qa_pairs):
            if not interview_id:
                interview_id = f"IVW-{i+1:05d}"
            
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
                "start_timestamp": format_timestamp_for_database(answer_seg.start_timestamp),
                "end_timestamp": format_timestamp_for_database(answer_seg.end_timestamp)
            }
            
            responses.append(response)
        
        return responses
        
    except Exception as e:
        logger.error(f"Error processing transcript: {e}")
        return []

def process_universal_csv_with_timestamps(csv_path, client_id, max_rows=None, save_to_db=True):
    """Process any CSV with transcripts and extract timestamps"""
    
    print("="*70)
    print("UNIVERSAL TIMESTAMP PROCESSING")
    print("="*70)
    
    # Load CSV
    print(f"\n1. Loading CSV: {csv_path}")
    try:
        df = pd.read_csv(csv_path)
        print(f"   ✅ Loaded {len(df)} rows")
    except Exception as e:
        print(f"   ❌ Error loading CSV: {e}")
        return
    
    # Check for required columns
    transcript_columns = ['Raw Transcript', 'Transcript', 'Full Transcript', 'Moderator Responses']
    transcript_column = None
    
    for col in transcript_columns:
        if col in df.columns:
            transcript_column = col
            break
    
    if not transcript_column:
        print(f"   ❌ No transcript column found. Available columns:")
        print(f"   {list(df.columns)}")
        return
    
    print(f"   ✅ Using transcript column: {transcript_column}")
    
    # Initialize database
    db = None
    if save_to_db:
        try:
            db = SupabaseDatabase()
            print("   ✅ Database connected")
        except Exception as e:
            print(f"   ❌ Database connection failed: {e}")
            return
    
    # Process interviews
    print(f"\n2. Processing interviews...")
    
    total_responses = 0
    total_with_timestamps = 0
    processed_interviews = 0
    
    df_to_process = df.head(max_rows) if max_rows else df
    
    for index, row in df_to_process.iterrows():
        try:
            print(f"\n   Processing interview {index + 1}/{len(df_to_process)}...")
            
            # Get transcript
            transcript = row.get(transcript_column, '')
            if not transcript or pd.isna(transcript):
                print(f"   ⚠️ Skipping: No transcript data")
                continue
            
            # Extract metadata (try different column names)
            company = (row.get('Interview Contact Company Name') or 
                     row.get('Company') or 
                     row.get('Company Name') or 
                     f'Company_{index + 1}')
            
            interviewee = (row.get('Interview Contact Full Name') or 
                          row.get('Interviewee') or 
                          row.get('Contact Name') or 
                          f'Interviewee_{index + 1}')
            
            deal_status = (row.get('Deal Status') or 
                          row.get('Status') or 
                          'closed_won')
            
            interview_date = (row.get('Completion Date') or 
                            row.get('Interview Date') or 
                            row.get('Date') or 
                            datetime.now().strftime('%Y-%m-%d'))
            
            interview_id = (row.get('Interview ID') or 
                          row.get('ID') or 
                          f'IVW-{index + 1:05d}')
            
            print(f"   📊 Company: {company}")
            print(f"   👤 Interviewee: {interviewee}")
            print(f"   🆔 Interview ID: {interview_id}")
            
            # Process transcript with universal parser
            responses = process_universal_transcript_with_timestamps(
                transcript, company, interviewee, deal_status, interview_date, client_id, interview_id
            )
            
            if responses:
                print(f"   ✅ Extracted {len(responses)} responses")
                total_responses += len(responses)
                processed_interviews += 1
                
                # Count responses with timestamps
                timestamped_responses = [r for r in responses if r.get('start_timestamp') or r.get('end_timestamp')]
                total_with_timestamps += len(timestamped_responses)
                print(f"   🎬 {len(timestamped_responses)} responses have timestamps")
                
                # Save to database
                if save_to_db and db:
                    for response in responses:
                        try:
                            db.save_core_response(response)
                        except Exception as e:
                            print(f"   ❌ Error saving response: {e}")
                    print(f"   💾 Saved to database")
            else:
                print(f"   ⚠️ No responses extracted")
            
        except Exception as e:
            print(f"   ❌ Error processing interview {index + 1}: {e}")
            continue
    
    # Final results
    print(f"\n" + "="*70)
    print("UNIVERSAL PROCESSING COMPLETE")
    print("="*70)
    
    print(f"📊 Total interviews: {len(df_to_process)}")
    print(f"✅ Successfully processed: {processed_interviews}")
    print(f"📝 Total responses: {total_responses}")
    print(f"🎬 Responses with timestamps: {total_with_timestamps}")
    
    if total_responses > 0:
        timestamp_percentage = (total_with_timestamps / total_responses) * 100
        print(f"📈 Timestamp coverage: {timestamp_percentage:.1f}%")
    
    if save_to_db:
        print(f"💾 All data saved to database with timestamps")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python universal_timestamp_processor.py <csv_file> [client_id] [max_rows] [save_to_db]")
        print("Example: python universal_timestamp_processor.py any_data.csv my_client 5 true")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    client_id = sys.argv[2] if len(sys.argv) > 2 else "default_client"
    max_rows = int(sys.argv[3]) if len(sys.argv) > 3 else None
    save_to_db = sys.argv[4].lower() == 'true' if len(sys.argv) > 4 else True
    
    process_universal_csv_with_timestamps(csv_path, client_id, max_rows, save_to_db)
