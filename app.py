import os
import sys
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed
from voc_pipeline.processor import process_transcript

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
        # gather your fixed metadata from user inputs or env
        client, company, interviewee, deal_status, date = (
            client,  # or stash in constants
            company,
            interviewee_name,
            deal_status,
            date_of_interview,
        )
        dfs = []
        with ThreadPoolExecutor(max_workers=5) as exec:
            futures = {
                exec.submit(
                    process_transcript,
                    path, client, company, interviewee, deal_status, date.strftime("%m/%d/%Y")
                ): path
                for path in uploaded_paths
            }
            for f in as_completed(futures):
                src = futures[f]
                try:
                    dfs.append(f.result())
                except Exception as e:
                    st.sidebar.error(f"❌ {src} failed: {e}")
        if dfs:
            df = pd.concat(dfs, ignore_index=True)
            # Save the combined DataFrame
            df.to_csv("response_data_table.csv", index=False)
            st.success("✅ All done!")
            st.dataframe(df)  # show the full table

# Create tabs for different views
tab1, tab2 = st.tabs(["Validated Quotes", "Response Data Table"])

with tab1:
    st.header("Validated Quotes")
    
    # Check for validated data first, then fallback to raw data
    if os.path.exists(VALIDATED_CSV) and os.path.getsize(VALIDATED_CSV) > 0:
        try:
            df = pd.read_csv(VALIDATED_CSV)
            if len(df) > 0:
                st.write(f"Showing {len(df)} validated quotes")
                st.dataframe(
                    df[[
                        "response_id","chunk_text","Subject","Question",
                        "deal_status","company","interviewee_name","date_of_interview"
                    ]]
                )
                if len(df) > 200:
                    st.info(f"Showing first 200 of {len(df)} records")
            else:
                st.warning("Validated quotes file is empty")
                # Fallback to raw data
                if os.path.exists("stage1_output.csv"):
                    df = pd.read_csv("stage1_output.csv")
                    st.write(f"Showing {len(df)} raw quotes (fallback)")
                    st.dataframe(df.head(200))
                else:
                    st.info("No data available. Upload & Process to get started.")
        except Exception as e:
            st.error(f"Error reading validated quotes: {e}")
            # Fallback to raw data
            if os.path.exists("stage1_output.csv"):
                df = pd.read_csv("stage1_output.csv")
                st.write(f"Showing {len(df)} raw quotes (fallback)")
                st.dataframe(df.head(200))
            else:
                st.info("No data available. Upload & Process to get started.")
    else:
        # No validated file, try raw data
        if os.path.exists("stage1_output.csv"):
            df = pd.read_csv("stage1_output.csv")
            st.write(f"Showing {len(df)} raw quotes")
            st.dataframe(df.head(200))
        else:
            st.info("No data available. Upload & Process to get started.")

with tab2:
    st.header("Response Data Table")
    if os.path.exists("response_data_table.csv") and os.path.getsize("response_data_table.csv") > 0:
        try:
            df2 = pd.read_csv("response_data_table.csv")
            if len(df2) > 0:
                st.write(f"Showing {len(df2)} response records")
                st.dataframe(df2)
                st.download_button(
                    "Download Response Table",
                    data=df2.to_csv(index=False),
                    file_name="response_data_table.csv"
                )
            else:
                st.warning("Response data table is empty")
        except Exception as e:
            st.error(f"Error reading response data table: {e}")
            st.info("The CSV file may be malformed. Try regenerating it.")
    else:
        st.info("Run the pipeline to generate the response data table.")
