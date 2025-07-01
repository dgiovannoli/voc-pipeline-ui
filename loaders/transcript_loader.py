# loaders/transcript_loader.py

import os
from typing import List, Dict
from docx import Document
from langchain_community.document_loaders import TextLoader
from langchain.schema import Document as LangDoc
# (If the above fails, try: from langchain_core.schema.document import Document as LangDoc)# (If the above fails, try: from langchain.schema import Document as LangDoc)
class TranscriptLoader:
    """
    Given a list of file paths (.txt or .docx), load each into one or more
    LangChain Documents with metadata, ready for chunking.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        from langchain_community.text_splitter import RecursiveCharacterTextSplitter

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

    def _load_docx(self, path: str) -> str:
        doc = Document(path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)

    def load_and_chunk(self, file_paths: List[str]) -> List[Dict]:
        """
        Returns a list of dicts: {text: <chunked text>, metadata: {...}}
        """
        docs: List[LangDoc] = []

        for path in file_paths:
            ext = os.path.splitext(path)[1].lower()
            if ext == ".docx":
                raw_text = self._load_docx(path)
                # wrap into a single LangDoc so splitter can chunk it
                docs.append(LangDoc(page_content=raw_text, metadata={"source": path}))
            elif ext == ".txt":
                loader = TextLoader(path, encoding="utf-8")
                docs.extend(loader.load_and_split(self.splitter))
            else:
                # skip unsupported types
                continue

        # now splitter works on LangDoc objects
        chunked = []
        for doc in docs:
            chunks = self.splitter.split_text(doc.page_content)
            for i, chunk in enumerate(chunks):
                chunked.append({
                    "text": chunk,
                    "metadata": {
                        **doc.metadata,
                        "chunk_index": i,
                    }
                })
        return chunked

