import pandas as pd
import os
from typing import List, Dict

class CSVLoader:
    """
    Loads a structured CSV (one row per response) and returns a list of dicts:
    { 'text': <verbatim response>, 'metadata': {...} }
    """
    def __init__(self):
        pass

    def load_and_chunk(self, file_paths: List[str]) -> List[Dict]:
        all_docs = []
        for path in file_paths:
            ext = os.path.splitext(path)[1].lower()
            if ext != ".csv":
                continue
            df = pd.read_csv(path)
            print(f"[DEBUG][CSVLoader] Loaded {len(df)} rows from {path}")
            print(f"[DEBUG][CSVLoader] Columns: {list(df.columns)}")
            if len(df) > 0:
                print(f"[DEBUG][CSVLoader] First row: {df.iloc[0].to_dict()}")
            for idx, row in df.iterrows():
                text = row.get("Verbatim Response", "")
                meta = {
                    "response_id": row.get("Response ID", f"row_{idx}"),
                    "question": row.get("Question", ""),
                    "key_insight": row.get("Key_Insight", ""),
                    "deal_status": row.get("Deal Status", ""),
                    "company_name": row.get("Company Name", ""),
                    "interviewee_name": row.get("Interviewee Name", ""),
                    "date_of_interview": row.get("Date of Interview", ""),
                    "source": path,
                    "chunk_index": idx,
                    "client_id": "Rev"
                }
                all_docs.append({"text": text, "metadata": meta})
        return all_docs 