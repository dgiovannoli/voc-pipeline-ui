import os
import sys
import subprocess
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed

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

# Show processing info
if uploads:
    st.sidebar.info(f"📊 **Processing Info:**\n"
                   f"• Files: {len(uploads)}\n"
                   f"• Model: gpt-4o-mini\n"
                   f"• Est. Cost: ~${len(uploads) * 0.002:.3f}\n"
                   f"• Est. Time: ~{len(uploads) * 0.5:.1f} minutes")

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
            # Progress tracking setup
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Process transcripts and capture output
            stage1_outputs = []
            total_files = len(uploaded_paths)
            
            status_text.text(f"Processing {total_files} files...")
            
            with ThreadPoolExecutor(max_workers=3) as ex:  # Rate limiting: max 3 concurrent
                futures = [
                  ex.submit(
                    subprocess.run,
                    [sys.executable, "-m", "voc_pipeline", "process_transcript",
                     path, client, company, interviewee_name, deal_status, date_of_interview.strftime("%m/%d/%Y")],
                    check=True, capture_output=True, text=True
                  )
                  for path in uploaded_paths
                ]
                
                # Track progress as files complete
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
            
            # Step 2: Combine all outputs and save to stage1_output.csv
            if stage1_outputs:
                # Get header from first output
                header = stage1_outputs[0].split('\n')[0]
                all_data = [header]
                
                # Add data rows from all outputs
                for output in stage1_outputs:
                    lines = output.strip().split('\n')
                    if len(lines) > 1:  # Has data beyond header
                        all_data.extend(lines[1:])  # Skip header, add data rows
                
                # Save combined output
                with open("stage1_output.csv", "w") as f:
                    f.write('\n'.join(all_data))
            
            # Step 3: Run validation
            status_text.text("Validating data...")
            progress_bar.progress(0.8)
            subprocess.run([
                sys.executable, "-m", "voc_pipeline", "validate",
                "--input", "stage1_output.csv",
                "--output", VALIDATED_CSV
            ], check=True)
            
            # Step 4: Build final table
            status_text.text("Building final table...")
            progress_bar.progress(0.9)
            subprocess.run([
                sys.executable, "-m", "voc_pipeline", "build-table",
                "--input", VALIDATED_CSV,
                "--output", "response_data_table.csv"
            ], check=True)
            
            # Complete
            progress_bar.progress(1.0)
            status_text.text("✅ Complete!")
            st.sidebar.success("✅ All interviews processed, validated, and table built!")
            
        except subprocess.CalledProcessError as e:
            st.sidebar.error(f"❌ Processing failed: {e}")
            st.sidebar.text(f"Error output: {e.stderr}")
        except Exception as e:
            st.sidebar.error(f"🔴 Unexpected error: {e}")

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
                        "Response ID","Verbatim Response","Subject","Question",
                        "Deal Status","Company Name","Interviewee Name","Date of Interview"
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
