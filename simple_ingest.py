#!/usr/bin/env python3
"""
Simple ingestion script to load CSV data into the database without Pinecone.
"""

import os
import sys
from supabase_database import SupabaseDatabase
from datetime import datetime
from loaders.csv_loader import CSVLoader

def simple_ingest(csv_path, client_id="Rev"):
    """Load CSV data directly into the database for client_id='Rev'."""
    print(f"Loading CSV: {csv_path}")
    print(f"Client ID: {client_id}")

    # Load CSV data using CSVLoader
    loader = CSVLoader()
    docs = loader.load_and_chunk([csv_path])
    print(f"Loaded {len(docs)} documents from CSVLoader.")
    if docs:
        print(f"First document metadata: {docs[0]['metadata']}")
        print(f"First document text: {docs[0]['text'][:200]}...")

    # Initialize database
    db = SupabaseDatabase()

    # Insert each document into core_responses
    for idx, doc in enumerate(docs):
        meta = doc["metadata"]
        response_data = {
            "client_id": meta.get("client_id", client_id),
            "response_id": meta.get("response_id", f"response_{idx}"),
            "question": meta.get("question", ""),
            "key_insight": meta.get("key_insight", ""),
            "verbatim_response": doc.get("text", ""),
            "deal_status": meta.get("deal_status", ""),
            "company": meta.get("company_name", ""),
            "interviewee_name": meta.get("interviewee_name", ""),
            "interview_date": meta.get("date_of_interview", ""),
            "file_source": meta.get("source", ""),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        try:
            db.save_core_response(response_data)
            print(f"Inserted response {idx + 1}/{len(docs)}")
        except Exception as e:
            print(f"Error inserting response {idx + 1}: {e}")
    print(f"✅ Successfully ingested {len(docs)} responses into Supabase for client_id={client_id}")

    # Now run Stage 2 to generate quotes
    print("\n🔄 Running Stage 2 to generate quotes...")
    os.system(f"python run_stage2.py --client_id {client_id}")

    # Now run Stage 3 to generate findings
    print("\n🔄 Running Stage 3 to generate findings...")
    os.system(f"python run_stage3.py --client_id {client_id}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simple_ingest.py <csv_path> [client_id]")
        sys.exit(1)
    csv_path = sys.argv[1]
    client_id = sys.argv[2] if len(sys.argv) > 2 else "Rev"
    simple_ingest(csv_path, client_id) 