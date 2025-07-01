import os
from typing import List, Dict
from langchain_community.document_loaders import TextLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

class TranscriptLoader:
    def __init__(self, chunk_size=500, chunk_overlap=100):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\\n\\n","\\n"," ",""],
        )

    def load_and_chunk(self, paths: List[str]) -> List[Dict]:
        docs = []
        for path in paths:
            ext = os.path.splitext(path)[1].lower()
            loader = TextLoader(path) if ext==".txt" else Docx2txtLoader(path)
            text = loader.load()[0].page_content
            chunks = self.splitter.split_text(text)
            meta = {
                "interview_id": os.path.basename(path),
                "speaker": "unknown",
                "deal_outcome": "unknown",
                "date": "unknown",
                "client_id": os.getenv("CLIENT_ID","unknown"),
                "source_type": "customer",
            }
            for i, c in enumerate(chunks):
                docs.append({"text": c, "metadata": {**meta, "chunk_index": i}})
        return docs
