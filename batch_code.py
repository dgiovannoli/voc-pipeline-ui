import csv
import os
import argparse
from loaders.transcript_loader import TranscriptLoader
from coders.response_coder import ResponseCoder

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

    # 2) Code quotes
    coder = ResponseCoder()
    rows = []
    for c in chunks:
        tagged = coder.code(c["text"], c["metadata"])
        # merge metadata into the row
        row = {**c["metadata"], **tagged}
        # Add external metadata to every record
        row["deal_status"] = args.deal_status
        row["company"] = args.company
        row["interviewee_name"] = args.interviewee_name
        row["date_of_interview"] = args.date_of_interview
        rows.append(row)

    # 3) Write output CSV with exact fieldnames from schema
    fieldnames = ["response_id", "verbatim_response", "subject", "question", "deal_status", "company", "interviewee_name", "date_of_interview"]
    
    # Filter rows to only include schema fields
    filtered_rows = []
    for row in rows:
        filtered_row = {field: row.get(field, "") for field in fieldnames}
        filtered_rows.append(filtered_row)
    
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered_rows)

    print(f"Wrote {len(rows)} rows to {args.output}")

if __name__ == "__main__":
    main()
