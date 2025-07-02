import csv
import os
import argparse
import concurrent.futures
import time
import re
from typing import List, Dict, Any
from loaders.transcript_loader import TranscriptLoader
from coders.response_coder import ResponseCoder

def is_substantive(text: str) -> bool:
    t = text.strip()
    if len(t) < 20:
        return False
    if re.match(r'^(Speaker \d+|Hi|Hello|How are you\?)', t):
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description="Stage 1: chunk & code quotes")
    parser.add_argument(
        "--client",
        required=True,
        help="Client name"
    )
    parser.add_argument(
        "--deal-status",
        required=True,
        help="Deal status"
    )
    parser.add_argument(
        "--company",
        required=True,
        help="Company name"
    )
    parser.add_argument(
        "--interviewee-name",
        required=True,
        help="Interviewee name"
    )
    parser.add_argument(
        "--date-of-interview",
        required=True,
        help="Date of interview (YYYY-MM-DD format)"
    )
    parser.add_argument(
        "--inputs", "-i",
        nargs="+",
        required=True,
        help="List of transcript file paths to ingest"
    )
    parser.add_argument(
        "--output", "-o",
        default="stage1_output.csv",
        help="CSV file to write coded quotes into"
    )
    args = parser.parse_args()

    # 1) Load & chunk
    loader = TranscriptLoader()
    chunks = loader.load_and_chunk(args.inputs)

    # 2) Code quotes with parallel processing
    # filter out non-substantive chunks (e.g. just "Speaker 1:")
    good_chunks = [c for c in chunks if is_substantive(c["text"])]
    print(f"Processing {len(good_chunks)} chunks...")
    start_time = time.time()
    rows = []
    coder = ResponseCoder()
    for i, c in enumerate(good_chunks):
        meta = c['metadata']
        # Compute the six required parameters
        response_id = f"{meta['company']}_{i+1}"
        chunk_text = c['text']
        company = meta['company']
        interviewee_name = meta['speaker']
        deal_status = meta['deal_outcome']
        date_of_interview = meta['date']
        
        tag: dict = coder.code(chunk_text, response_id, company, interviewee_name, deal_status, date_of_interview)
        if not tag:
            continue
        rows.append(tag)
    processing_time = time.time() - start_time
    print(f"Processing completed in {processing_time:.2f} seconds")

    # 3) Write output CSV with exact fieldnames from schema
    fieldnames = ['response_id','chunk_text','company','interviewee_name','deal_status','date_of_interview']
    
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {args.output}")

def process_chunks_parallel(chunks: List[Dict[str, Any]], args) -> List[Dict[str, Any]]:
    """Process chunks in parallel with batching for better performance."""
    # Determine optimal batch size and worker count
    num_chunks = len(chunks)
    max_workers = min(4, num_chunks)  # Limit to 4 workers to avoid rate limits
    batch_size = max(1, num_chunks // max_workers)
    
    print(f"Using {max_workers} workers with batch size {batch_size}")
    
    # Create batches
    batches = [chunks[i:i + batch_size] for i in range(0, num_chunks, batch_size)]
    
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit batch processing tasks
        future_to_batch = {
            executor.submit(process_batch, batch, args): batch 
            for batch in batches
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_batch):
            batch = future_to_batch[future]
            try:
                batch_rows = future.result()
                rows.extend(batch_rows)
                print(f"Completed batch of {len(batch_rows)} chunks")
            except Exception as e:
                print(f"Batch processing failed: {e}")
                # Fallback to sequential processing for failed batch
                fallback_rows = process_batch_sequential(batch, args)
                rows.extend(fallback_rows)
    
    return rows

def process_batch(batch: List[Dict[str, Any]], args) -> List[Dict[str, Any]]:
    """Process a batch of chunks with a dedicated coder instance."""
    coder = ResponseCoder()
    rows = []
    
    for c in batch:
        try:
            tagged = coder.code(c["text"], c["metadata"])
            # merge metadata into the row
            row = {**c["metadata"], **tagged}
            # Add external metadata to every record
            row["deal_status"] = args.deal_status
            row["company"] = args.company
            row["interviewee_name"] = args.interviewee_name
            row["date_of_interview"] = args.date_of_interview
            rows.append(row)
        except Exception as e:
            print(f"Error processing chunk: {e}")
            # Create fallback row with basic info
            fallback_row = create_fallback_row(c, args)
            rows.append(fallback_row)
    
    return rows

def process_batch_sequential(batch: List[Dict[str, Any]], args) -> List[Dict[str, Any]]:
    """Fallback sequential processing for failed batches."""
    coder = ResponseCoder()
    rows = []
    
    for c in batch:
        try:
            tagged = coder.code(c["text"], c["metadata"])
            row = {**c["metadata"], **tagged}
            row["deal_status"] = args.deal_status
            row["company"] = args.company
            row["interviewee_name"] = args.interviewee_name
            row["date_of_interview"] = args.date_of_interview
            rows.append(row)
        except Exception as e:
            print(f"Sequential fallback failed for chunk: {e}")
            fallback_row = create_fallback_row(c, args)
            rows.append(fallback_row)
    
    return rows

def create_fallback_row(chunk: Dict[str, Any], args) -> Dict[str, Any]:
    """Create a fallback row when processing fails."""
    return {
        "response_id": f"resp_{chunk['metadata'].get('interview_id', 'unknown')}_{chunk['metadata'].get('chunk_index', 0)}",
        "verbatim_response": chunk["text"][:500],  # Truncate if too long
        "subject": "processing_error",
        "question": "fallback_entry",
        "deal_status": args.deal_status,
        "company": args.company,
        "interviewee_name": args.interviewee_name,
        "date_of_interview": args.date_of_interview
    }

if __name__ == "__main__":
    main()
