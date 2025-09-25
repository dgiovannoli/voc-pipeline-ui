"""
Enhanced Stage 1 Processor with Timestamp Support
Integrates timestamp extraction into the existing stage 1 processing pipeline.
"""

import json
import re
import sys
from typing import List, Dict, Tuple, Optional
from enhanced_timestamp_processor import process_chunk_with_timestamps
from prompts.core_extraction_with_timestamps import get_core_extraction_prompt_with_timestamps

def process_chunk_with_timestamp_support(
    chunk: str,
    chunk_index: int,
    company: str,
    interviewee: str,
    deal_status: str,
    date_of_interview: str,
    client: str,
    found_qa: bool = False,
    chain=None
) -> List[Dict]:
    """
    Process a transcript chunk with timestamp support
    
    Args:
        chunk: Raw transcript chunk
        chunk_index: Index of the chunk
        company: Company name
        interviewee: Interviewee name
        deal_status: Deal status
        date_of_interview: Interview date
        client: Client ID
        found_qa: Whether this is a Q&A format transcript
        chain: LLM chain for processing
        
    Returns:
        List of processed responses with timestamps
    """
    try:
        # Extract timestamps and clean the chunk
        cleaned_chunk, timestamp_info = process_chunk_with_timestamps(chunk, found_qa)
        
        if not cleaned_chunk:
            print(f"📋 Chunk {chunk_index} filtered: no content after cleaning", file=sys.stderr)
            return []
        
        # Skip low-value responses
        if is_low_value_response(cleaned_chunk):
            print(f"📋 Chunk {chunk_index} filtered: low-value response", file=sys.stderr)
            return []
        
        # Prepare input for the chain with timestamp information
        base_response_id = normalize_response_id(company, interviewee, chunk_index, client)
        
        # Create enhanced chain input with timestamp context
        chain_input = {
            "chunk_text": cleaned_chunk,
            "response_id": base_response_id,
            "key_insight": "",  # Let the LLM fill this in
            "company": company,
            "company_name": company,
            "interviewee_name": interviewee,
            "deal_status": deal_status,
            "date_of_interview": date_of_interview,
            "timestamp_context": {
                "start_timestamp": timestamp_info.get('start_timestamp'),
                "end_timestamp": timestamp_info.get('end_timestamp'),
                "raw_timestamps": timestamp_info.get('raw_timestamps', [])
            }
        }
        
        # Get response from LLM with retries
        chunk_responses = []
        for attempt in range(3):
            try:
                # Use the enhanced prompt with timestamp support
                prompt = get_core_extraction_prompt_with_timestamps(
                    response_id=base_response_id,
                    company=company,
                    interviewee_name=interviewee,
                    deal_status=deal_status,
                    date_of_interview=date_of_interview,
                    chunk_text=cleaned_chunk
                )
                
                # For now, we'll use the existing chain but with enhanced prompt
                # In a full implementation, you'd modify the chain to use the new prompt
                response = chain.invoke(chain_input)
                
                # Extract content from AIMessage object
                if hasattr(response, 'content'):
                    raw = response.content.strip()
                else:
                    raw = str(response).strip()
                
                if not raw:
                    continue
                
                # Parse response - could be single object or array
                parsed = json.loads(raw)
                
                if isinstance(parsed, list):
                    for i, item in enumerate(parsed):
                        if not item.get('verbatim_response', '').strip():
                            continue
                        # Ensure unique response ID
                        item['response_id'] = f"{base_response_id}_{i+1}"
                        
                        # Add timestamp information if not present
                        if 'start_timestamp' not in item:
                            item['start_timestamp'] = timestamp_info.get('start_timestamp')
                        if 'end_timestamp' not in item:
                            item['end_timestamp'] = timestamp_info.get('end_timestamp')
                        
                        chunk_responses.append(item)
                else:
                    if parsed.get('verbatim_response', '').strip():
                        parsed['response_id'] = f"{base_response_id}_1"
                        
                        # Add timestamp information if not present
                        if 'start_timestamp' not in parsed:
                            parsed['start_timestamp'] = timestamp_info.get('start_timestamp')
                        if 'end_timestamp' not in parsed:
                            parsed['end_timestamp'] = timestamp_info.get('end_timestamp')
                        
                        chunk_responses.append(parsed)
                
                print(f"✅ Chunk {chunk_index}: extracted {len(chunk_responses)} responses with timestamps", file=sys.stderr)
                break
                
            except json.JSONDecodeError as e:
                print(f"⚠️ Chunk {chunk_index} attempt {attempt+1}: JSON decode error", file=sys.stderr)
                if attempt == 2:  # Last attempt
                    print(f"❌ Chunk {chunk_index}: failed after 3 attempts", file=sys.stderr)
                    break
            except Exception as e:
                print(f"⚠️ Chunk {chunk_index} attempt {attempt+1}: {e}", file=sys.stderr)
                if attempt == 2:  # Last attempt
                    print(f"❌ Chunk {chunk_index}: failed after 3 attempts", file=sys.stderr)
                    break
        
        return chunk_responses
        
    except Exception as e:
        print(f"❌ Error processing chunk {chunk_index}: {e}", file=sys.stderr)
        return []

def normalize_response_id(company: str, interviewee: str, chunk_index: int, client: str) -> str:
    """Normalize response ID for consistency"""
    # Clean company and interviewee names
    clean_company = re.sub(r'[^a-zA-Z0-9]', '_', company.lower())
    clean_interviewee = re.sub(r'[^a-zA-Z0-9]', '_', interviewee.lower())
    
    return f"{client}_{clean_company}_{clean_interviewee}_{chunk_index}"

def is_low_value_response(text: str) -> bool:
    """Check if response is low value and should be filtered out"""
    if not text or len(text.strip()) < 10:
        return True
    
    # Check for common low-value patterns
    low_value_patterns = [
        r'^(yes|no|ok|okay|sure|thanks?|thank you|you\'re welcome)$',
        r'^(uh|um|hmm|ah|oh)$',
        r'^(i don\'t know|i\'m not sure|not really)$',
        r'^(that\'s it|that\'s all|nothing else)$'
    ]
    
    text_lower = text.lower().strip()
    for pattern in low_value_patterns:
        if re.match(pattern, text_lower):
            return True
    
    return False

def enhance_database_save_with_timestamps(response_data: Dict[str, any]) -> Dict[str, any]:
    """
    Enhance response data with timestamp fields for database storage
    
    Args:
        response_data: Original response data
        
    Returns:
        Enhanced response data with timestamp fields
    """
    enhanced_data = response_data.copy()
    
    # Add timestamp fields if they exist
    if 'start_timestamp' in response_data:
        enhanced_data['start_timestamp'] = response_data['start_timestamp']
    if 'end_timestamp' in response_data:
        enhanced_data['end_timestamp'] = response_data['end_timestamp']
    
    return enhanced_data

def test_enhanced_processor():
    """Test the enhanced stage 1 processor"""
    sample_chunk = """Speaker 1 (01:00):
[00:01:00] Hi, Brian. What was your current solution at the time?

Speaker 2 (01:10):
[00:01:10] We had our own warehouse, own software, own negotiated rates.

Speaker 1 (01:15):
[00:01:15] And what prompted you to consider options outside of that?

Speaker 2 (01:20):
[00:01:20] We're at the point where I either need to open up other warehouses or find someone that has a three PL network that I can rent little spaces from to take advantage of economies of scale at shipping."""
    
    print("Testing enhanced stage 1 processor...")
    
    # Mock chain for testing
    class MockChain:
        def invoke(self, input_data):
            class MockResponse:
                def __init__(self):
                    self.content = json.dumps([{
                        "response_id": "test_1",
                        "verbatim_response": "We had our own warehouse, own software, own negotiated rates.",
                        "subject": "Current Solution",
                        "question": "What was your current solution at the time?",
                        "start_timestamp": "00:01:10",
                        "end_timestamp": "00:01:15",
                        "deal_status": "closed_won",
                        "company": "Test Company",
                        "interviewee_name": "Test Interviewee",
                        "date_of_interview": "2024-01-01"
                    }])
            return MockResponse()
    
    mock_chain = MockChain()
    
    responses = process_chunk_with_timestamp_support(
        chunk=sample_chunk,
        chunk_index=0,
        company="Test Company",
        interviewee="Test Interviewee",
        deal_status="closed_won",
        date_of_interview="2024-01-01",
        client="test_client",
        found_qa=False,
        chain=mock_chain
    )
    
    print(f"Extracted {len(responses)} responses:")
    for i, response in enumerate(responses):
        print(f"  {i+1}. {response.get('subject')} [{response.get('start_timestamp')}-{response.get('end_timestamp')}]: {response.get('verbatim_response')[:50]}...")

if __name__ == "__main__":
    test_enhanced_processor()
