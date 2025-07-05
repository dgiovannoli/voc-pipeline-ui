#!/usr/bin/env python3
import csv
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="Stage 1 Passthrough: Copy all stage1 rows without filtering")
    parser.add_argument(
        "--input", "-i",
        default="stage1_output.csv",
        help="Input CSV file path containing stage1 output (default: stage1_output.csv)"
    )
    parser.add_argument(
        "--output", "-o",
        default="passthrough_quotes.csv",
        help="Output CSV file path for passthrough quotes (default: passthrough_quotes.csv)"
    )
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found")
        return 1
    
    # Read all rows from stage1 output
    rows = []
    with open(args.input, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)
    
    # Write all rows to passthrough output
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Passthrough complete: {len(rows)} rows written to {args.output}")
    return 0

if __name__ == "__main__":
    exit(main()) 