#!/usr/bin/env python3
import os
import sys
import argparse
from ingestion.ingest import ingest_to_pinecone
from dotenv import load_dotenv

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="VoC Pipeline - Run ingestion and processing steps")
    parser.add_argument(
        "--step", "-s",
        required=True,
        choices=["ingest"],
        help="Pipeline step to execute"
    )
    parser.add_argument(
        "--inputs", "-i",
        nargs="+",
        required=True,
        help="List of input file paths to process"
    )
    
    args = parser.parse_args()
    
    if args.step == "ingest":
        ingest_to_pinecone(args.inputs)
    else:
        print(f"Unknown step: {args.step}")
        sys.exit(1)

if __name__ == "__main__":
    main()
