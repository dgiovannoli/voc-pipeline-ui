"""
Enhanced Timestamp Processing for VOC Pipeline
Integrates timestamp extraction with existing transcript processing.
"""

import re
from typing import List, Dict, Tuple, Optional
from timestamp_parser import TimestampParser, TimestampSegment

def extract_timestamps_before_cleaning(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Extract timestamps from transcript before cleaning and return cleaned text with timestamp info
    
    Args:
        text: Raw transcript text
        
    Returns:
        Tuple of (cleaned_text, timestamp_info)
        timestamp_info contains: start_timestamp, end_timestamp, raw_timestamps
    """
    parser = TimestampParser()
    
    # Parse the transcript into segments
    segments = parser.parse_transcript_segments(text)
    
    # Extract timestamp information
    timestamp_info = {
        'start_timestamp': None,
        'end_timestamp': None,
        'raw_timestamps': []
    }
    
    if segments:
        # Get start timestamp from first segment
        if segments[0].start_timestamp:
            timestamp_info['start_timestamp'] = segments[0].start_timestamp
        
        # Get end timestamp from last segment
        if segments[-1].end_timestamp:
            timestamp_info['end_timestamp'] = segments[-1].end_timestamp
        elif segments[-1].start_timestamp:
            timestamp_info['end_timestamp'] = segments[-1].start_timestamp
        
        # Collect all raw timestamps
        for segment in segments:
            if segment.raw_timestamps:
                timestamp_info['raw_timestamps'].extend(segment.raw_timestamps)
    
    # Clean the text using existing logic but preserve timestamp info
    cleaned_text = clean_verbatim_response_with_timestamps(text)
    
    return cleaned_text, timestamp_info

def clean_verbatim_response_with_timestamps(text: str, interviewer_names=None) -> str:
    """
    Clean verbatim response while preserving timestamp information for later extraction
    
    This is a modified version of the original clean_verbatim_response function
    that removes timestamps from the text but doesn't strip them completely
    """
    if interviewer_names is None:
        interviewer_names = ["Q:", "A:", "Interviewer:", "Drew Giovannoli:", "Brian:", "Yusuf Elmarakby:"]
    
    lines = text.splitlines()
    cleaned_lines = []
    
    for line in lines:
        l = line.strip()
        # Remove interview titles/headings
        if l.lower().startswith("an interview with") or l.lower().startswith("interview with"):
            continue
        # Remove speaker labels, timestamps, Q:/A: tags
        if any(l.startswith(name) for name in interviewer_names):
            continue
        if re.match(r'^Speaker \d+ \(\d{2}:\d{2}\):', l):
            continue
        if re.match(r'^\(\d{2}:\d{2}\):', l):
            continue
        # Skip lines that are just questions (but keep questions that are part of longer content)
        if l.endswith("?") and len(l) < 50:
            continue
        cleaned_lines.append(line)
    
    cleaned = " ".join(cleaned_lines).strip()
    
    # Remove leading speaker timestamps like "Speaker 1 (01:52):"
    cleaned = re.sub(r'^Speaker \d+ \(\d{2}:\d{2}\):\s*', '', cleaned)
    # Remove trailing timestamps like "(03:07):"
    cleaned = re.sub(r'\(\d{2}:\d{2}\):\s*$', '', cleaned)
    # Remove speaker labels at start of lines: "Drew Giovannoli:", etc.
    cleaned = re.sub(r'^(Speaker \d+|Drew Giovannoli|Brian|Yusuf Elmarakby):\s*', '', cleaned, flags=re.MULTILINE)
    # Remove question context - look for patterns like "Q: What do you think?" and remove
    cleaned = re.sub(r'^Q:\s*[^A]*?(?=A:|$)', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'^Question:\s*[^A]*?(?=Answer:|$)', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    # Remove interviewer questions that might be mixed in
    cleaned = re.sub(r'Interviewer:\s*[^I]*?(?=Interviewee:|$)', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove inline timestamps [00:01:00] from the text
    cleaned = re.sub(r'\[\d{1,2}:\d{2}(?::\d{2})?\]', '', cleaned)
    
    # Clean up extra whitespace and newlines, but preserve paragraph breaks
    cleaned = re.sub(r'\n+', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Remove disfluencies
    cleaned = remove_disfluencies(cleaned)
    
    # Ensure we have meaningful content (be less strict)
    if len(cleaned) < 5:
        return ""
    
    return cleaned

def remove_disfluencies(text: str) -> str:
    """Remove common disfluencies unless they are part of a longer phrase"""
    # Remove standalone "um", "uh", "like" but keep them in context
    text = re.sub(r'\b(um|uh|like)\b(?=\s|$)', '', text)
    return text

def process_chunk_with_timestamps(chunk: str, found_qa: bool = False) -> Tuple[str, Dict[str, str]]:
    """
    Process a transcript chunk and extract timestamps
    
    Args:
        chunk: Raw transcript chunk
        found_qa: Whether this is a Q&A format transcript
        
    Returns:
        Tuple of (cleaned_chunk, timestamp_info)
    """
    if found_qa:
        # For Q&A format, clean aggressively and extract timestamps
        cleaned_chunk, timestamp_info = extract_timestamps_before_cleaning(chunk)
        if not cleaned_chunk:
            return "", {}
    else:
        # For speaker-based transcripts, extract timestamps first
        cleaned_chunk, timestamp_info = extract_timestamps_before_cleaning(chunk)
        if not cleaned_chunk:
            return "", {}
    
    return cleaned_chunk, timestamp_info

def test_enhanced_processor():
    """Test the enhanced timestamp processor"""
    sample_chunk = """Speaker 1 (01:00):
[00:01:00] Hi, Brian.

Speaker 2 (01:10):
Hey, how's it going?

Speaker 1 (01:11):
Well, how are you?

Speaker 2 (01:12):
Good, good.

Speaker 1 (01:16):
The coolest part about my job, especially with Ship Out, is I get to meet the coolest products all day long. [00:01:30] I love this part."""
    
    print("Testing enhanced timestamp processor...")
    cleaned_text, timestamp_info = process_chunk_with_timestamps(sample_chunk, found_qa=False)
    
    print(f"Cleaned text: {cleaned_text[:100]}...")
    print(f"Start timestamp: {timestamp_info.get('start_timestamp')}")
    print(f"End timestamp: {timestamp_info.get('end_timestamp')}")
    print(f"Raw timestamps: {timestamp_info.get('raw_timestamps')}")

if __name__ == "__main__":
    test_enhanced_processor()
