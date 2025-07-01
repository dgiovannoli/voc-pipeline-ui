import os
import sys
import subprocess

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# 1) Load env vars (for future use)
load_dotenv()

# 2) Simple password gate
password = st.sidebar.text_input("Enter app password", type="password")
if password != "treasure23":
    st.sidebar.error("🔒 Incorrect password")
    st.stop()

# 3) Configuration
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
VALIDATED_CSV = "validated_quotes.csv"

st.title("VoC Pipeline Explorer")

# ─── Sidebar: Upload & Process ───────────────────────────────────────────────
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
            # 1: ingest
            subprocess.run(
                [sys.executable, "run_pipeline.py", "--step", "ingest", "--inputs"] + uploaded_paths,
                check=True,
            )
            # 2: stage1 code
            subprocess.run(
                [sys.executable, "batch_code.py", "--output", "stage1_output.csv"],
                check=True,
            )
            # 3: stage2 validate
            subprocess.run(
                [sys.executable, "batch_validate.py", "--input", "stage1_output.csv", "--output", VALIDATED_CSV],
                check=True,
            )
            st.sidebar.success("✅ Processing complete")
        except subprocess.CalledProcessError as e:
            st.sidebar.error(f"Pipeline error: {e}")
        except Exception as e:
            st.sidebar.error(f"Unexpected error: {e}")

# ─── Main: Data Explorer ─────────────────────────────────────────────────────
st.header("Validated Quotes")

if os.path.exists(VALIDATED_CSV):
    df = pd.read_csv(VALIDATED_CSV)
    # Allow filtering by criteria
    all_criteria = sorted(df["criteria"].dropna().unique())
    selected = st.multiselect("Filter by criteria", all_criteria, default=all_criteria)
    if selected:
        df = df[df["criteria"].isin(selected)]
    st.write(f"Showing {len(df)} quotes")
    st.dataframe(df.reset_index(drop=True).head(200))
else:
    st.info("No `validated_quotes.csv` found yet. Upload & Process to get started.")
