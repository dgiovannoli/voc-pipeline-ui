import os
import sys
import subprocess
from datetime import date

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
PASSTHROUGH_CSV = "passthrough_quotes.csv"

st.title("VoC Pipeline Explorer")

# Metadata inputs at the top of the sidebar
st.sidebar.header("Metadata")
client = st.sidebar.text_input("Client")
deal_status = st.sidebar.selectbox("Deal Status", ["closed_won", "closed_lost", "no_decision"])
company = st.sidebar.text_input("Company")
interviewee_name = st.sidebar.text_input("Interviewee Name")
date_of_interview = st.sidebar.date_input("Date of Interview", value=date.today())

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
                [sys.executable, "batch_code.py", 
                 "--client", client,
                 "--deal-status", deal_status,
                 "--company", company,
                 "--interviewee-name", interviewee_name,
                 "--date-of-interview", date_of_interview.strftime("%Y-%m-%d"),
                 "--inputs"] + uploaded_paths + ["--output", "stage1_output.csv"],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            proc = subprocess.run(
                [sys.executable, "batch_validate.py", "--input", "stage1_output.csv", "--output", VALIDATED_CSV],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            # Run passthrough after validation
            proc = subprocess.run(
                [sys.executable, "batch_passthrough.py", "--input", "stage1_output.csv", "--output", PASSTHROUGH_CSV],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            # Generate final response data table
            proc = subprocess.run(
                [sys.executable, "batch_table.py", "--input", "stage1_output.csv", "--output", "response_data_table.csv"],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            st.sidebar.success("✅ Processing complete")
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode("utf-8", errors="replace")
            st.sidebar.error("❌ Ingestion pipeline failed:")
            st.sidebar.text(err)
        except Exception as e:
            st.sidebar.error(f"🔴 Unexpected error: {e}")

# Create tabs for different views
tab1, tab2 = st.tabs(["Validated Quotes", "Response Data Table"])

with tab1:
    st.header("Validated Quotes")
    validated_exists = os.path.exists(VALIDATED_CSV)
    passthrough_exists = os.path.exists(PASSTHROUGH_CSV)
    validated_rows = 0
    passthrough_rows = 0

    df_validated = None
    df_passthrough = None

    if validated_exists:
        df_validated = pd.read_csv(VALIDATED_CSV)
        validated_rows = len(df_validated)
    if passthrough_exists:
        df_passthrough = pd.read_csv(PASSTHROUGH_CSV)
        passthrough_rows = len(df_passthrough)

    if validated_exists and validated_rows > 0:
        all_criteria = sorted(df_validated["criteria"].dropna().unique())
        selected = st.multiselect("Filter by criteria", all_criteria, default=all_criteria)
        if selected:
            df_validated = df_validated[df_validated["criteria"].isin(selected)]
        st.write(f"Showing {len(df_validated)} quotes")
        st.dataframe(df_validated.head(200))
    # Fallback: show passthrough if validated is empty but passthrough has rows
    elif passthrough_exists and passthrough_rows > 0:
        st.warning("Validated quotes are empty, but raw coded quotes are available. Displaying passthrough quotes as fallback.")
        st.write(f"Showing {min(200, passthrough_rows)} passthrough quotes")
        st.dataframe(df_passthrough.head(200))
    else:
        st.info("No `validated_quotes.csv` found yet. Upload & Process to get started.")

with tab2:
    if os.path.exists("response_data_table.csv"):
        df2 = pd.read_csv("response_data_table.csv")
        st.dataframe(df2)
        st.download_button(
            "Download Response Table",
            data=df2.to_csv(index=False),
            file_name="response_data_table.csv"
        )
    else:
        st.info("Run the pipeline to generate the response data table.")

if os.path.exists(VALIDATED_CSV) and os.path.getsize(VALIDATED_CSV)>0:
    df = pd.read_csv(VALIDATED_CSV)
else:
    df = pd.read_csv("stage1_output.csv")

st.write(f"Showing {len(df)} records")
st.dataframe(df)
