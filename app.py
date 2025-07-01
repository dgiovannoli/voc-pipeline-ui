import os
import sys
import subprocess

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

password = st.sidebar.text_input("Enter app password", type="password")
if password != "treasure23":
    st.sidebar.error("🔒 Incorrect password")
    st.stop()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
VALIDATED_CSV = "validated_quotes.csv"

st.title("VoC Pipeline Explorer")

st.sidebar.header("1) Upload Interviews")
uploads = st.sidebar.file_uploader(
    "Select .txt or .docx files", type=["txt", "docx"], accept_multiple_files=True
)

uploaded_paths = []
if uploads:
    for f in uploads:
        dest = os.path.join(UPLOAD_DIR, f.name)
        with open(dest, "wb") as out:
            out.write(f.getbuffer())
        uploaded_paths.append(dest)
    st.sidebar.success(f"🗄️ Saved {len(uploaded_paths)} file(s)")

    if st.sidebar.button("▶️ Process"):
        try:
            proc = subprocess.run(
                [sys.executable, "run_pipeline.py", "--step", "ingest", "--inputs"] + uploaded_paths,
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            proc = subprocess.run(
                [sys.executable, "batch_code.py", "--output", "stage1_output.csv"],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            proc = subprocess.run(
                [sys.executable, "batch_validate.py", "--input", "stage1_output.csv", "--output", VALIDATED_CSV],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            st.sidebar.success("✅ Processing complete")
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode("utf-8", errors="replace")
            st.sidebar.error("❌ Ingestion pipeline failed:")
            st.sidebar.text(err)
        except Exception as e:
            st.sidebar.error(f"🔴 Unexpected error: {e}")

st.header("Validated Quotes")
if os.path.exists(VALIDATED_CSV):
    df = pd.read_csv(VALIDATED_CSV)
    all_criteria = sorted(df["criteria"].dropna().unique())
    selected = st.multiselect("Filter by criteria", all_criteria, default=all_criteria)
    if selected:
        df = df[df["criteria"].isin(selected)]
    st.write(f"Showing {len(df)} quotes")
    st.dataframe(df.head(200))
else:
    st.info("No `validated_quotes.csv` found yet. Upload & Process to get started.")
