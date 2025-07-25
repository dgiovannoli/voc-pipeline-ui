from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
import os
import openai
from pinecone import Pinecone
import uvicorn
import logging

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "client-voc-embeddings")

# Initialize OpenAI and Pinecone
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

app = FastAPI()

logging.basicConfig(level=logging.INFO)

# Utility: Generate embedding
def get_embedding(text):
    response = openai_client.embeddings.create(input=text, model="text-embedding-ada-002")
    return response.data[0].embedding

# Utility: Upsert to Pinecone
def upsert_to_pinecone(record, embedding, record_type="finding"):
    metadata = {
        "type": record_type,
        "client_id": record.get("client_id"),
        "id": record.get("id"),
        "finding_statement": record.get("finding_statement", ""),
        "verbatim_response": record.get("verbatim_response", ""),
        "theme_statement": record.get("theme_statement", "")
    }
    index.upsert(vectors=[{
        "id": f"{record_type}-{record.get('id')}",
        "values": embedding,
        "metadata": metadata
    }])

@app.post("/webhook")
async def supabase_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    logging.info(f"Received webhook payload: {payload}")
    # Supabase sends {record: {...}} for new/updated rows
    record = payload.get("record") or payload
    if not record:
        return JSONResponse({"error": "No record found in payload"}, status_code=400)
    # Determine type (finding, response, theme) based on payload or table
    record_type = record.get("type") or "finding"
    # Choose text to embed
    text = record.get("finding_statement") or record.get("verbatim_response") or record.get("theme_statement")
    if not text:
        return JSONResponse({"error": "No text to embed in record"}, status_code=400)
    # Process embedding and upsert in background
    def embed_and_upsert():
        try:
            embedding = get_embedding(text)
            upsert_to_pinecone(record, embedding, record_type)
            logging.info(f"Upserted {record_type} {record.get('id')} to Pinecone.")
        except Exception as e:
            logging.error(f"Embedding/upsert failed: {e}")
    background_tasks.add_task(embed_and_upsert)
    return {"status": "ok", "message": f"Embedding/upsert for {record_type} {record.get('id')} scheduled."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080) 