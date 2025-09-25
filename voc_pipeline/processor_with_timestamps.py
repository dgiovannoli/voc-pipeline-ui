"""
Enhanced VOC Pipeline Processor with Timestamp Support
Integrates timestamp extraction into the existing stage 1 processing pipeline.
"""

import os
import sys
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import Docx2txtLoader

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our enhanced timestamp processing functions
from enhanced_timestamp_processor import process_chunk_with_timestamps
from prompts.core_extraction_with_timestamps import get_core_extraction_prompt_with_timestamps

def _process_transcript_parallel_with_timestamps(
    full_text: str,
    client: str,
    company: str,
    interviewee: str,
    deal_status: str,
    date_of_interview: str,
    max_workers: int = 3
) -> str:
    """
    Process transcript using parallel chunk processing with timestamp support.
    
    Args:
        full_text: The full transcript text
        client: Client identifier
        company: Company name
        interviewee: Interviewee name
        deal_status: Deal status
        date_of_interview: Date of interview
        max_workers: Maximum number of parallel workers
        
    Returns:
        CSV string with extracted responses including timestamps
    """
    print(f"🚀 Starting parallel Stage 1 processing with timestamps using {max_workers} workers", file=sys.stderr)
    start_time = time.time()
    
    # Create LLM chain (RunnableSequence) - using ChatOpenAI for gpt-4o-mini
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(
        model_name="gpt-4o-mini",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        max_tokens=4096,
        temperature=0.1
    )
    
    # 2) Use quality-focused chunking targeting ~5 insights per interview (7K tokens)
    # Balance between context and granularity for consistent high-quality insights
    qa_segments, found_qa = create_qa_aware_chunks(full_text, target_tokens=7000, overlap_tokens=600)
    print(f"🔍 Passing {len(qa_segments)} chunks to LLM with parallel processing and timestamp extraction", file=sys.stderr)
    
    # 3) Run parallel chunk processing with timestamp support
    all_quality_rows = []
    
    def process_single_chunk_with_timestamps(chunk_info):
        """Process a single chunk in parallel with timestamp extraction - thread-safe implementation"""
        chunk_index, chunk = chunk_info
        try:
            # Filter out non-Q&A chunks
            if not is_qa_chunk(chunk, found_qa):
                print(f"📋 Chunk {chunk_index} filtered: not Q&A content", file=sys.stderr)
                return []
            
            # Extract timestamps and clean the chunk text
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
            
            # Use the enhanced prompt with timestamp support
            prompt = get_core_extraction_prompt_with_timestamps(
                response_id=base_response_id,
                company=company,
                interviewee_name=interviewee,
                deal_status=deal_status,
                date_of_interview=date_of_interview,
                chunk_text=cleaned_chunk
            )
            
            # Create a simple chain for this specific prompt
            chain = llm
            
            # Get response from LLM with retries
            chunk_responses = []
            for attempt in range(3):
                try:
                    # Use the enhanced prompt directly
                    response = chain.invoke(prompt)
                    
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
                            if 'start_timestamp' not in item or not item['start_timestamp']:
                                item['start_timestamp'] = timestamp_info.get('start_timestamp')
                            if 'end_timestamp' not in item or not item['end_timestamp']:
                                item['end_timestamp'] = timestamp_info.get('end_timestamp')
                            
                            chunk_responses.append(item)
                    else:
                        if parsed.get('verbatim_response', '').strip():
                            parsed['response_id'] = f"{base_response_id}_1"
                            
                            # Add timestamp information if not present
                            if 'start_timestamp' not in parsed or not parsed['start_timestamp']:
                                parsed['start_timestamp'] = timestamp_info.get('start_timestamp')
                            if 'end_timestamp' not in parsed or not parsed['end_timestamp']:
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
    
    # Process chunks in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all chunks for processing
        future_to_chunk = {
            executor.submit(process_single_chunk_with_timestamps, (i, chunk)): i 
            for i, chunk in enumerate(qa_segments)
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_chunk):
            chunk_index = future_to_chunk[future]
            try:
                chunk_responses = future.result()
                if chunk_responses:
                    all_quality_rows.extend(chunk_responses)
            except Exception as e:
                print(f"❌ Chunk {chunk_index} failed: {e}", file=sys.stderr)
    
    # 4) Convert to CSV format
    if not all_quality_rows:
        print("❌ No valid responses extracted", file=sys.stderr)
        return ""
    
    # Sort by response_id to maintain order
    all_quality_rows.sort(key=lambda x: x.get('response_id', ''))
    
    # Convert to CSV
    csv_output = convert_responses_to_csv(all_quality_rows)
    
    end_time = time.time()
    processing_time = end_time - start_time
    print(f"✅ Parallel processing completed in {processing_time:.2f} seconds", file=sys.stderr)
    print(f"📊 Extracted {len(all_quality_rows)} responses with timestamps", file=sys.stderr)
    
    return csv_output

def convert_responses_to_csv(responses: List[Dict]) -> str:
    """Convert response data to CSV format including timestamp fields"""
    if not responses:
        return ""
    
    # Get all possible field names from all responses
    all_fields = set()
    for response in responses:
        all_fields.update(response.keys())
    
    # Define the order of fields (put important ones first)
    field_order = [
        'response_id', 'verbatim_response', 'subject', 'question',
        'start_timestamp', 'end_timestamp',  # New timestamp fields
        'deal_status', 'company', 'interviewee_name', 'date_of_interview',
        'key_insight', 'findings', 'value_realization', 'implementation_experience',
        'risk_mitigation', 'competitive_advantage', 'customer_success',
        'product_feedback', 'service_quality', 'decision_factors',
        'pain_points', 'success_metrics', 'future_plans'
    ]
    
    # Add any remaining fields
    for field in sorted(all_fields):
        if field not in field_order:
            field_order.append(field)
    
    # Create CSV header
    csv_lines = [','.join(f'"{field}"' for field in field_order)]
    
    # Add data rows
    for response in responses:
        row = []
        for field in field_order:
            value = response.get(field, '')
            # Escape quotes and wrap in quotes
            if isinstance(value, str):
                value = value.replace('"', '""')
            row.append(f'"{value}"')
        csv_lines.append(','.join(row))
    
    return '\n'.join(csv_lines)

# Import the existing utility functions from the original processor
from voc_pipeline.processor import (
    create_qa_aware_chunks,
    is_qa_chunk,
    is_low_value_response,
    normalize_response_id
)

def process_transcript_with_timestamps(transcript_path, client, company, interviewee, deal_status, date_of_interview):
    """Process a transcript with timestamp support and output CSV data."""
    _process_transcript_impl_with_timestamps(transcript_path, client, company, interviewee, deal_status, date_of_interview)

def _process_transcript_impl_with_timestamps(
    transcript_path: str,
    client: str,
    company: str,
    interviewee: str,
    deal_status: str,
    date_of_interview: str,
) -> None:
    """
    Load the transcript, run the enhanced processing with timestamps,
    and emit raw CSV to stdout.
    """
    # Load environment variables
    load_dotenv()
    
    # Debug: Check if API key is loaded
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in environment")
        return
    
    # Load transcript
    if transcript_path.lower().endswith(".docx"):
        loader = Docx2txtLoader(transcript_path)
        # 1) Load full transcript
        docs = loader.load()
        full_text = docs[0].page_content
    else:
        full_text = open(transcript_path, encoding="utf-8").read()
    
    if not full_text.strip():
        print("ERROR: Transcript is empty")
        return
    
    # Use enhanced parallel processing with timestamps for Stage 1
    result = _process_transcript_parallel_with_timestamps(full_text, client, company, interviewee, deal_status, date_of_interview)
    
    # Output results
    if result:
        print(result)
    else:
        print("ERROR: No valid responses extracted")

if __name__ == "__main__":
    # Example usage
    if len(sys.argv) != 7:
        print("Usage: python processor_with_timestamps.py <transcript_path> <client> <company> <interviewee> <deal_status> <date_of_interview>")
        sys.exit(1)
    
    transcript_path, client, company, interviewee, deal_status, date_of_interview = sys.argv[1:7]
    process_transcript_with_timestamps(transcript_path, client, company, interviewee, deal_status, date_of_interview)
