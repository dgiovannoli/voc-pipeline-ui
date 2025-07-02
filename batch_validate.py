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
    for row in reader:
        try:
            result = v.validate(row)
            if result:
                # Map old schema to new schema
                new_row = {
                    "response_id": result.get("response_id", f"resp_{result.get('interview_id', 'unknown')}_{result.get('chunk_index', 0)}"),
                    "verbatim_response": result.get("verbatim_response", result.get("text", "")),
                    "subject": result.get("subject", "unknown"),
                    "question": result.get("question", "unknown"),
                    "deal_status": result.get("deal_status", "unknown"),
                    "company_name": result.get("company_name", result.get("company", "unknown")),
                    "interviewee_name": result.get("interviewee_name", "unknown"),
                    "date_of_interview": result.get("date_of_interview", "2024-01-01"),
                }
                validated.append(new_row)
            else:
                # dropped with no return
                print(f"DROPPED (no return): quote_id={row.get('quote_id')} row={row}")
                continue
        except Exception as e:
            # validation threw an error
            print(f"ERROR in validate() for quote_id={row.get('quote_id')}: {e}")
            continue

    # these must match your new eight-column schema:
    fieldnames = [
      "response_id","verbatim_response","subject","question",
      "deal_status","company_name","interviewee_name","date_of_interview",
    ]
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(validated)
    
    print(f"Validated {len(validated)} quotes, wrote to {args.output}")

if __name__ == "__main__":
    main()
