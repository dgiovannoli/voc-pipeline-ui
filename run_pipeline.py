#!/usr/bin/env python3
import os
import sys
from ingestion.ingest import ingest_to_pinecone
from dotenv import load_dotenv

load_dotenv()

def main():
    if "--step" not in sys.argv:
        print("Usage: run_pipeline.py --step ingest --inputs file1 [file2 ...]")
        sys.exit(1)
    step = sys.argv[sys.argv.index("--step") + 1]
    if step == "ingest":
        files = sys.argv[sys.argv.index("--inputs") + 1:]
        ingest_to_pinecone(files)
    else:
        print(f"Unknown step: {step}")

if __name__ == "__main__":
    main()
