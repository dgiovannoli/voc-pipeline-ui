#!/usr/bin/env python3
import pandas as pd
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="Generate final response data table")
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input CSV file (validated or raw)"
    )
    parser.add_argument(
        "--output", "-o",
        default="response_data_table.csv",
        help="Output CSV file path"
    )
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found")
        return 1
    
    # Read the input CSV into pandas
    df = pd.read_csv(args.input)
    
    # Define the exact column order from our eight-column schema
    schema_columns = ["response_id", "verbatim_response", "subject", "question", "deal_status", "company", "interviewee_name", "date_of_interview"]
    
    # Reorder columns to match schema (only include columns that exist in the dataframe)
    existing_columns = [col for col in schema_columns if col in df.columns]
    if existing_columns:
        df = df[existing_columns]
    
    # Write out response_data_table.csv with header and rows intact
    df.to_csv(args.output, index=False)
    
    print(f"Generated response data table with {len(df)} rows: {args.output}")
    return 0

if __name__ == "__main__":
    exit(main()) 