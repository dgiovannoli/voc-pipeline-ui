import os
import sys
import subprocess
from datetime import date, datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import pathlib
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import re

load_dotenv()

BASE = pathlib.Path(__file__).parent
UPLOAD_DIR = BASE / "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
VALIDATED_CSV = BASE / "validated_quotes.csv"
PASSTHROUGH_CSV = BASE / "passthrough_quotes.csv"
RESPONSE_TABLE_CSV = BASE / "response_data_table.csv"
STAGE1_CSV = BASE / "stage1_output.csv"

st.title("VoC Pipeline Explorer")

# Remove metadata input fields
# st.sidebar.header("Metadata")
# client = st.sidebar.text_input("Client")
# deal_status = st.sidebar.selectbox("Deal Status", ["closed_won", "closed_lost", "no_decision"])
# company = st.sidebar.text_input("Company")
# interviewee_name = st.sidebar.text_input("Interviewee Name")
# date_of_interview = st.sidebar.date_input("Date of Interview", value=date.today())

st.sidebar.info("ℹ️ Metadata is now auto-populated from the pipeline and transcript. No manual entry required.")

st.sidebar.header("1) Upload Interviews")
uploads = st.sidebar.file_uploader(
    "Select .txt or .docx files", type=["txt", "docx"], accept_multiple_files=True
)

# Debug: Show file mtime and head
for label, path in [("Validated", VALIDATED_CSV), ("Response Table", RESPONSE_TABLE_CSV)]:
    if os.path.exists(path):
        mtime = os.path.getmtime(path)
        st.sidebar.text(f"{label} last write: {datetime.fromtimestamp(mtime)}")
        try:
            st.sidebar.code(subprocess.check_output(["head", "-n", "3", str(path)]).decode())
        except Exception:
            pass

# Live CSV loader with TTL
@st.cache_data(ttl=1, show_spinner=False)
def load_csv(path):
    return pd.read_csv(path)

uploaded_paths = []

def extract_client_from_filename(filename):
    name = filename.rsplit('.', 1)[0]
    match = re.search(r'at ([^.,]+)', name, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r'Interview with ([^.,-]+)', name, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return name.strip()

if uploads:
    for f in uploads:
        dest = UPLOAD_DIR / f.name
        with open(dest, "wb") as out:
            out.write(f.getbuffer())
        uploaded_paths.append(str(dest))
    st.sidebar.success(f"🗄️ Saved {len(uploaded_paths)} file(s)")

    if st.sidebar.button("▶️ Process"):
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            stage1_outputs = []
            total_files = len(uploaded_paths)
            status_text.text(f"Processing {total_files} files...")
            with ThreadPoolExecutor(max_workers=3) as ex:
                futures = [
                  ex.submit(
                    subprocess.run,
                    [sys.executable, "-m", "voc_pipeline", "process_transcript",
                     path,
                     extract_client_from_filename(os.path.basename(path)),  # client
                     extract_client_from_filename(os.path.basename(path)),  # company
                     "", "", ""],
                    check=True, capture_output=True, text=True
                  )
                  for path in uploaded_paths
                ]
                completed = 0
                for f in as_completed(futures):
                    try:
                        result = f.result()
                        stage1_outputs.append(result.stdout)
                        completed += 1
                        progress = completed / total_files
                        progress_bar.progress(progress)
                        status_text.text(f"Processed {completed}/{total_files} files...")
                    except Exception as e:
                        st.warning(f"File failed: {e}")
                        completed += 1
                        progress = completed / total_files
                        progress_bar.progress(progress)
                        continue
            if stage1_outputs:
                header = stage1_outputs[0].split('\n')[0]
                all_data = [header]
                for output in stage1_outputs:
                    lines = output.strip().split('\n')
                    if len(lines) > 1:
                        all_data.extend(lines[1:])
                with open(STAGE1_CSV, "w") as f:
                    f.write('\n'.join(all_data))
            status_text.text("Validating data...")
            progress_bar.progress(0.8)
            subprocess.run([
                sys.executable, "-m", "voc_pipeline", "validate",
                "--input", str(STAGE1_CSV),
                "--output", str(VALIDATED_CSV)
            ], check=True)
            status_text.text("Building final table...")
            progress_bar.progress(0.9)
            subprocess.run([
                sys.executable, "-m", "voc_pipeline", "build-table",
                "--input", str(VALIDATED_CSV),
                "--output", str(RESPONSE_TABLE_CSV)
            ], check=True)
            progress_bar.progress(1.0)
            status_text.text("✅ Complete!")
            st.sidebar.success("✅ All interviews processed, validated, and table built!")
            st.experimental_rerun()
        except subprocess.CalledProcessError as e:
            st.sidebar.error(f"❌ Processing failed: {e}")
            st.sidebar.text(f"Error output: {e.stderr}")
        except Exception as e:
            st.sidebar.error(f"🔴 Unexpected error: {e}")

# Create tabs for different views
tab1, tab2 = st.tabs(["Validated Quotes", "Response Data Table"])

with tab1:
    st.header("Validated Quotes")
    st.caption("Main columns only. Metadata is auto-populated.")
    if os.path.exists(VALIDATED_CSV) and os.path.getsize(VALIDATED_CSV) > 0:
        try:
            df = load_csv(VALIDATED_CSV)
            if len(df) > 0:
                st.write(f"Showing {len(df)} validated quotes")
                main_cols = [
                    "Response ID", "Subject", "Key Insight", "Question", "Verbatim Response",
                    "Deal Status", "Company Name", "Interviewee Name", "Date of Interview"
                ]
                st.dataframe(df[main_cols])
                if len(df) > 200:
                    st.info(f"Showing first 200 of {len(df)} records")
            else:
                st.warning("Validated quotes file is empty")
                if os.path.exists(STAGE1_CSV):
                    df = load_csv(STAGE1_CSV)
                    st.write(f"Showing {len(df)} raw quotes (fallback)")
                    st.dataframe(df.head(200))
                else:
                    st.info("No data available. Upload & Process to get started.")
        except Exception as e:
            st.error(f"Error reading validated quotes: {e}")
            if os.path.exists(STAGE1_CSV):
                df = load_csv(STAGE1_CSV)
                st.write(f"Showing {len(df)} raw quotes (fallback)")
                st.dataframe(df.head(200))
            else:
                st.info("No data available. Upload & Process to get started.")
    else:
        if os.path.exists(STAGE1_CSV):
            df = load_csv(STAGE1_CSV)
            st.write(f"Showing {len(df)} raw quotes")
            st.dataframe(df.head(200))
        else:
            st.info("No data available. Upload & Process to get started.")

with tab2:
    st.header("Response Data Table")
    st.caption("Full table with all columns.")
    if os.path.exists(RESPONSE_TABLE_CSV) and os.path.getsize(RESPONSE_TABLE_CSV) > 0:
        try:
            df2 = load_csv(RESPONSE_TABLE_CSV)
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
