import os
from dotenv import load_dotenv
import pinecone
from pinecone import Pinecone as PineconeClient, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from loaders.transcript_loader import TranscriptLoader

def clean_metadata_for_pinecone(metadata):
    """Remove None values from metadata as Pinecone only accepts string, number, boolean, or list of strings"""
    cleaned = {}
    for key, value in metadata.items():
        if value is not None:
            cleaned[key] = value
    return cleaned

def ingest_to_pinecone(paths):
    load_dotenv()

    # 1) Load + chunk
    loader = TranscriptLoader()
    docs = loader.load_and_chunk(paths)

    # —————————— ensure every chunk has interview_id & chunk_index ——————————
    for idx, d in enumerate(docs):
        meta = d.get("metadata", {})
        # default interview_id to filename
        if "interview_id" not in meta:
            src = meta.get("source") or d.get("source") or paths[0]
            meta["interview_id"] = os.path.splitext(os.path.basename(src))[0]
        # default chunk_index to its position
        if "chunk_index" not in meta:
            meta["chunk_index"] = idx
        d["metadata"] = meta
    texts = [d["text"] for d in docs]
    metadatas = [d["metadata"] for d in docs]

    # 2) Initialize Pinecone v2 client
    pine_api = os.getenv("PINECONE_API_KEY")
    pine_env = os.getenv("PINECONE_ENVIRONMENT")
    client = PineconeClient(api_key=pine_api, endpoint=os.getenv("PINECONE_ENDPOINT"))

    index_name = os.getenv("PINECONE_INDEX_NAME")
    # 3) Ensure index exists
    existing = client.list_indexes().names()
    if index_name not in existing:
        spec = ServerlessSpec(cloud="aws", region=pine_env)
        client.create_index(name=index_name, dimension=1536, metric="cosine", spec=spec)

    # 4) Create embeddings
    embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
    vectors = embeddings.embed_documents(texts)

    # 5) Upsert in batches
    idx = client.Index(index_name)
    batch = []
    for i, (vec, meta) in enumerate(zip(vectors, metadatas)):
        vid = f"{meta['interview_id']}_{meta.get('chunk_index', i)}"
        # Clean metadata to remove None values before sending to Pinecone
        cleaned_meta = clean_metadata_for_pinecone(meta)
        batch.append((vid, vec, cleaned_meta))
        if len(batch) == 100:
            idx.upsert(vectors=batch)
            batch = []
    if batch:
        idx.upsert(vectors=batch)

    print(f"Ingested {len(texts)} chunks into Pinecone index '{index_name}'")

if __name__ == "__main__":
    import fire
    fire.Fire({"ingest": ingest_to_pinecone})
