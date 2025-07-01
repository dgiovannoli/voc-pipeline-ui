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
        result = v.validate(row)
        if result:
            validated.append(result)

    # Preserve all original columns + the two new JSON columns
    fieldnames = reader.fieldnames + ["validated_evidence", "quality_report"]
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(validated)
    
    print(f"Validated {len(validated)} quotes, wrote to {args.output}")

if __name__ == "__main__":
    main()
