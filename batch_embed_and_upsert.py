import os
import openai
import pinecone
import pandas as pd
from supabase_database import SupabaseDatabase
from dotenv import load_dotenv

# Load environment variables and Streamlit secrets
load_dotenv()

# Load API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-west1-gcp")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "client-voc-embeddings")
PINECONE_REGION = os.getenv("PINECONE_REGION", "us-west-2")

openai.api_key = OPENAI_API_KEY

# Use new Pinecone client
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key=PINECONE_API_KEY)

# Ensure index exists
if PINECONE_INDEX not in pc.list_indexes().names():
    pc.create_index(
        name=PINECONE_INDEX,
        dimension=3072,  # text-embedding-3-large is 3072 dims
        metric='cosine',
        spec=ServerlessSpec(cloud='aws', region=PINECONE_REGION)
    )

index = pc.Index(PINECONE_INDEX)

def get_text_for_embedding(record, record_type):
    if record_type == "response":
        return record.get("verbatim_response") or ""
    elif record_type == "finding":
        return record.get("finding_statement") or ""
    elif record_type == "theme":
        return record.get("theme_statement") or ""
    return ""

def upsert_records(records, record_type, client_id):
    batch = []
    for record in records:
        record_id = record.get("id") or record.get("response_id") or record.get("finding_id") or record.get("theme_id")
        if not record_id:
            continue
        text = get_text_for_embedding(record, record_type)
        if not text:
            continue
        # Generate embedding (openai>=1.0.0)
        try:
            response = openai.embeddings.create(input=text, model="text-embedding-ada-002")
            embedding = response.data[0].embedding
        except Exception as e:
            print(f"❌ Error embedding {record_type} {record_id}: {e}")
            continue
        # Prepare Pinecone upsert
        vector_id = f"{client_id}:{record_type}:{record_id}"
        metadata = {"client_id": client_id, "type": record_type, "record_id": record_id}
        batch.append((vector_id, embedding, metadata))
        if len(batch) >= 50:
            index.upsert(vectors=batch)
            batch = []
    if batch:
        index.upsert(vectors=batch)

def main():
    db = SupabaseDatabase()
    # Get all unique client_ids
    client_ids = set()
    for table in ["stage1_data_responses", "stage3_findings", "stage4_themes"]:
        df = db.supabase.table(table).select("client_id").execute()
        if hasattr(df, 'data') and df.data:
            client_ids.update([row['client_id'] for row in df.data if row.get('client_id')])
    print(f"Found client_ids: {client_ids}")
    for client_id in client_ids:
        print(f"\nProcessing client: {client_id}")
        # Responses
        responses = db.get_stage1_data_responses(client_id)
        if not responses.empty:
            print(f"  Upserting {len(responses)} responses...")
            upsert_records(responses.to_dict('records'), "response", client_id)
        # Findings
        findings = db.get_stage3_findings(client_id)
        if not findings.empty:
            print(f"  Upserting {len(findings)} findings...")
            upsert_records(findings.to_dict('records'), "finding", client_id)
        # Themes
        themes = db.get_themes(client_id)
        if not themes.empty:
            print(f"  Upserting {len(themes)} themes...")
            upsert_records(themes.to_dict('records'), "theme", client_id)
    print("\n✅ Batch embedding and upsert complete.")

if __name__ == "__main__":
    main() 