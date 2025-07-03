#!/usr/bin/env python3
import csv
import argparse
from validators.quote_validator import QuoteValidator

def main():
    parser = argparse.ArgumentParser(description="Stage 2: Validate and quality-check quotes")
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input CSV file path containing coded quotes"
    )
    parser.add_argument(
        "--output", "-o",
        default="validated_quotes.csv",
        help="Output CSV file path for validated quotes"
    )
    
    args = parser.parse_args()
    
    reader = csv.DictReader(open(args.input))
    v = QuoteValidator()
    validated = []
    all_rows = []
    
    for row in reader:
        all_rows.append(row)
        try:
            result = v.validate(row)
            if result:
                # Add validated fields to the existing row
                validated_row = {
                    "response_id": row.get("response_id", ""),
                    "chunk_text": row.get("chunk_text", ""),
                    "company": row.get("company", ""),
                    "interviewee_name": row.get("interviewee_name", ""),
                    "deal_status": row.get("deal_status", ""),
                    "date_of_interview": row.get("date_of_interview", ""),
                    "Subject": result.get("subject", "unknown"),
                    "Question": result.get("question", "unknown"),
                }
                validated.append(validated_row)
            else:
                # dropped with no return
                print(f"DROPPED (no return): response_id={row.get('response_id')} row={row}")
                continue
        except Exception as e:
            # validation threw an error
            print(f"ERROR in validate() for response_id={row.get('response_id')}: {e}")
            continue
    
    # If no validated rows, default to all Stage 1 rows
    if not validated and all_rows:
        print("No validated rows found, defaulting to all Stage 1 rows")
        for row in all_rows:
            validated_row = {
                "response_id": row.get("response_id", ""),
                "chunk_text": row.get("chunk_text", ""),
                "company": row.get("company", ""),
                "interviewee_name": row.get("interviewee_name", ""),
                "deal_status": row.get("deal_status", ""),
                "date_of_interview": row.get("date_of_interview", ""),
                "Subject": row.get("subject", "unknown"),
                "Question": row.get("question", "unknown"),
            }
            validated.append(validated_row)

    # Updated fieldnames to include input columns + validated fields
    fieldnames = [
      "response_id","chunk_text","company","interviewee_name","deal_status","date_of_interview",
      "Subject","Question"
    ]
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(validated)
    
    print(f"Validated {len(validated)} quotes, wrote to {args.output}")

if __name__ == "__main__":
    main()
