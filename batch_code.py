#!/usr/bin/env python3
import csv, os
from loaders.transcript_loader import TranscriptLoader
from coders.response_coder import ResponseCoder

def main():
    chunks = TranscriptLoader().load_and_chunk(["samples/interview1.txt"])
    coder = ResponseCoder()
    rows = []
    for c in chunks:
        tags = coder.code(c["text"], c["metadata"])
        merged = { **c["metadata"], **tags }
        rows.append(merged)

    fieldnames = [
        "interview_id","speaker","deal_outcome","date","client_id","source_type",
        "quote_id","criteria","swot_theme","journey_phase","text"
    ]
    with open("stage1_output.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    main()
