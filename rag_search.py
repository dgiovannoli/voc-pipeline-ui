import os
import openai
from pinecone import Pinecone
import streamlit as st

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or st.secrets["OPENAI_API_KEY"]
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY") or st.secrets["PINECONE_API_KEY"]
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "client-voc-embeddings")

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

def get_query_embedding(query):
    response = openai_client.embeddings.create(input=query, model="text-embedding-ada-002")
    return response.data[0].embedding

def pinecone_rag_search(query, client_id, top_k=8):
    query_emb = get_query_embedding(query)
    results = index.query(
        vector=query_emb,
        top_k=top_k,
        filter={"client_id": client_id},
        include_metadata=True
    )
    return results["matches"]

def build_rag_context(matches):
    context = ""
    for m in matches:
        meta = m["metadata"]
        if meta["type"] == "response":
            context += f"Response: {meta.get('verbatim_response', '')}\n"
        elif meta["type"] == "finding":
            context += f"Finding: {meta.get('finding_statement', '')}\n"
        elif meta["type"] == "theme":
            context += f"Theme: {meta.get('theme_statement', '')}\n"
    return context 