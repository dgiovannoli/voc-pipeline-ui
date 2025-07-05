import os
import sys
import subprocess
from datetime import date, datetime
import pathlib
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import re
from database import VOCDatabase
from prompts.core_extraction import CORE_EXTRACTION_PROMPT

load_dotenv()

# Helper functions
def extract_interviewee_and_company(filename):
    """
    Extract interviewee and company from filename.
    Example: 'Interview with Ben Evenstad, Owner at Evenstad Law.docx' -> ('Ben Evenstad', 'Evenstad Law')
    """
    base = os.path.basename(filename).replace('.docx', '').replace('.txt', '')
    if base.lower().startswith("interview with "):
        base = base[len("interview with "):]
    parts = [p.strip() for p in base.split(",")]
    interviewee = parts[0] if parts else "Unknown"
    company = "Unknown"
    for part in parts[1:]:
        match = re.search(r'at (.+)', part, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            break
    return interviewee, company

def save_uploaded_files(uploaded_files, upload_dir="uploads"):
    """
    Save uploaded Streamlit files to disk and return a list of file paths.
    """
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    saved_paths = []
    for uploaded_file in uploaded_files:
        file_path = os.path.join(upload_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        saved_paths.append(file_path)
    return saved_paths

@st.cache_data(ttl=1, show_spinner=False)
def load_csv(path):
    try:
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"Error loading CSV from {path}: {e}")
        return pd.DataFrame()

def process_files():
    """Process uploaded files using the modular pipeline CLI"""
    if not st.session_state.uploaded_paths:
        raise Exception("No files uploaded")
    
    all_results = []
    processed_count = 0
    
    for i, path in enumerate(st.session_state.uploaded_paths):
        interviewee, company = extract_interviewee_and_company(os.path.basename(path))
        
        # Create temporary output file for this file
        temp_output = BASE / f"temp_output_{i}.csv"
        
        result = subprocess.run([
            sys.executable, "-m", "voc_pipeline.modular_cli", "extract-core",
            path,
            company if company else "Unknown",
            interviewee if interviewee else "Unknown",
            "closed_won",
            "2024-01-01",
            "-o", str(temp_output)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            st.error(f"Processing failed for {os.path.basename(path)}!\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}")
            # Clean up temp files
            for temp_file in [BASE / f"temp_output_{j}.csv" for j in range(len(st.session_state.uploaded_paths))]:
                if temp_file.exists():
                    temp_file.unlink()
            return
        
        # Load and combine results
        if temp_output.exists() and temp_output.stat().st_size > 0:
            try:
                df_temp = pd.read_csv(temp_output)
                all_results.append(df_temp)
                processed_count += 1
                st.success(f"✅ Processed {os.path.basename(path)}: {len(df_temp)} responses")
            except Exception as e:
                st.warning(f"⚠️ Could not read results from {os.path.basename(path)}: {e}")
        
        # Clean up temp file
        if temp_output.exists():
            temp_output.unlink()
    
    # Combine all results
    if all_results:
        combined_df = pd.concat(all_results, ignore_index=True)
        combined_df.to_csv(STAGE1_CSV, index=False)
        st.success(f"🎉 Successfully processed {processed_count} files with {len(combined_df)} total responses")
    else:
        st.error("Processing failed: No output was generated from any files. Please check your input files and try again.")
        return
    
    st.session_state.current_step = 2

def validate_and_build():
    """Run validation and build final table"""
    if os.path.exists(STAGE1_CSV):
        # Validate
        subprocess.run([
            sys.executable, "-m", "voc_pipeline", "validate",
            "--input", str(STAGE1_CSV),
            "--output", str(VALIDATED_CSV)
        ], check=True)
        
        # Build table
        subprocess.run([
            sys.executable, "-m", "voc_pipeline", "build-table",
            "--input", str(VALIDATED_CSV),
            "--output", str(RESPONSE_TABLE_CSV)
        ], check=True)

def load_prompt_template():
    prompt_path = os.path.join("prompts", "core_extraction.py")
    try:
        with open(prompt_path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Could not load prompt template: {e}"

PROCESSING_DETAILS = """
### Processing Details

How the pipeline processes your interviews (16K-optimized version):

**Batching & Parallel Processing:**
- Multiple interviews are processed in parallel using Python's `ThreadPoolExecutor` for speed and efficiency.
- Each file is handled as a separate job, so you can upload and process many interviews at once.

**Advanced Chunking & Segmentation (16K Optimized):**
- Uses token-based chunking with ~2K tokens per chunk (vs previous 2K character chunks)
- Q&A-aware segmentation that preserves conversation boundaries and context
- Intelligent overlap of 200 tokens to maintain continuity between chunks
- Preserves full Q&A exchanges and speaker turns within chunks
- Adaptive chunking that respects token limits while maximizing context

**Enhanced LLM Processing:**
- Each chunk is sent to GPT-3.5-turbo-16k with comprehensive context
- Extracts 3-5 insights per chunk (vs previous 1 insight per chunk)
- Preserves much longer verbatim responses (200-800 words vs previous 20-50 words)
- Focuses on detailed customer experiences, quantitative feedback, and specific examples

**Improved Content Extraction:**
- Prioritizes detailed customer experiences with specific scenarios and examples
- Captures quantitative feedback (metrics, timelines, ROI discussions)
- Preserves comparative analysis and competitive evaluations
- Maintains integration requirements and workflow details

**Quality Assurance:**
- Enhanced validation for richer, more contextually complete responses
- Quality logging tracks response length and content preservation
- Flags responses that lose too much context during processing

**Performance:**
- Fewer API calls due to larger chunks (more efficient token usage)
- Higher quality insights due to better context preservation
- Richer verbatim responses with full context and examples

---
This pipeline is optimized for the 16K token context window to deliver significantly richer insights and more complete verbatim responses.
"""

# Page configuration
st.set_page_config(
    page_title="VOC Pipeline",
    page_icon="🎯",
    layout="wide"
)

# Simple CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .step-card {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        border: 2px solid #e9ecef;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .step-active {
        border-color: #667eea;
        background: #f8f9ff;
    }
    .metric-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        border-left: 4px solid #667eea;
    }
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 2rem;
    }
</style>
""", unsafe_allow_html=True)

# File paths
BASE = pathlib.Path(__file__).parent
UPLOAD_DIR = BASE / "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
VALIDATED_CSV = BASE / "validated_quotes.csv"
RESPONSE_TABLE_CSV = BASE / "response_data_table.csv"
STAGE1_CSV = BASE / "stage1_output.csv"

# Initialize database and session state
if 'db' not in st.session_state:
    st.session_state.db = VOCDatabase()

if 'uploaded_paths' not in st.session_state:
    st.session_state.uploaded_paths = []

if 'current_step' not in st.session_state:
    st.session_state.current_step = 1

# Header
# st.markdown("""
# <div class="main-header">
#     <h1>🎯 VOC Pipeline</h1>
#     <p>Transform customer interviews into actionable insights</p>
# </div>
# """, unsafe_allow_html=True)

# Progress indicator
# col1, col2, col3 = st.columns(3)
# with col1:
#     step1_active = st.session_state.current_step == 1
#     st.markdown(f"""
#     <div class="step-card {'step-active' if step1_active else ''}">
#         <h3>📁 Upload & Process</h3>
#         <p>Upload and process files</p>
#     </div>
#     """, unsafe_allow_html=True)
#
# with col2:
#     step2_active = st.session_state.current_step == 2
#     st.markdown(f"""
#     <div class="step-card {'step-active' if step2_active else ''}">
#         <h3>✅ Validate</h3>
#         <p>Validate & enrich</p>
#     </div>
#     """, unsafe_allow_html=True)
#
# with col3:
#     step3_active = st.session_state.current_step == 3
#     st.markdown(f"""
#     <div class="step-card {'step-active' if step3_active else ''}">
#         <h3>📊 Export</h3>
#         <p>Download results</p>
#     </div>
#     """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.info("\u2139\ufe0f Metadata is now auto-populated from the pipeline and transcript. No manual entry required.")
    st.header("1) Upload Interviews")
    uploads = st.file_uploader("Select .txt or .docx files", type=["txt", "docx"], accept_multiple_files=True, key="uploads")
    if uploads:
        st.session_state.uploaded_paths = save_uploaded_files(uploads)
        st.success(f"{len(uploads)} files uploaded successfully")
        for f in uploads:
            st.write(f"- {f.name} ({f.size//1024}KB)")
    else:
        st.session_state.uploaded_paths = []
    st.header("2) Process Files")
    process_btn = st.button("\u25B6\ufe0f Process Files", type="primary", use_container_width=True)
    # Progress bar placeholder
    progress_placeholder = st.empty()
    if 'progress' not in st.session_state:
        st.session_state.progress = 0.0
    progress_placeholder.progress(st.session_state.progress, text=f"Processing: {int(st.session_state.progress*100)}%" if st.session_state.progress > 0 else "Idle")

# --- MAIN AREA ---
st.title("Buried Wins Fantastical Interview Parser")
tabs = st.tabs(["Validated Quotes", "Response Data Table", "Prompt Template", "Processing Details"])

# --- PROCESSING LOGIC ---
def process_files_with_progress():
    """Process uploaded files using the modular pipeline CLI, updating progress bar."""
    import time
    if not st.session_state.uploaded_paths:
        raise Exception("No files uploaded")
    all_dfs = []
    n = len(st.session_state.uploaded_paths)
    for i, path in enumerate(st.session_state.uploaded_paths):
        interviewee, company = extract_interviewee_and_company(os.path.basename(path))
        tmp_out = f"tmp_{i}_output.csv"
        result = subprocess.run([
            sys.executable, "-m", "voc_pipeline.modular_cli", "extract-core",
            path,
            company if company else "Unknown",
            interviewee if interviewee else "Unknown",
            "closed_won",
            "2024-01-01",
            "-o", tmp_out
        ], capture_output=True, text=True)
        if result.returncode != 0:
            st.error(f"Processing failed for {os.path.basename(path)}!\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}")
            continue
        if os.path.exists(tmp_out) and os.path.getsize(tmp_out) > 0:
            df = pd.read_csv(tmp_out)
            all_dfs.append(df)
            os.remove(tmp_out)
        st.session_state.progress = (i+1)/n
        progress_placeholder.progress(st.session_state.progress, text=f"Processing: {int(st.session_state.progress*100)}%")
        time.sleep(0.1)
    if all_dfs:
        df_all = pd.concat(all_dfs, ignore_index=True)
        df_all.to_csv(STAGE1_CSV, index=False)
    else:
        st.error("No processed data found.")
    st.session_state.progress = 0.0
    progress_placeholder.progress(st.session_state.progress, text="Idle")

# --- MAIN LOGIC ---
if process_btn:
    with st.spinner("Processing files..."):
        process_files_with_progress()

# --- TABS CONTENT ---
with tabs[0]:
    # Validated Quotes (core responses)
    if not os.path.exists(STAGE1_CSV) or os.path.getsize(STAGE1_CSV) == 0:
        st.info("No processed data found. Upload and process files to see validated quotes.")
    else:
        df = load_csv(STAGE1_CSV)
        core_cols = [
            'response_id', 'verbatim_response', 'subject', 'question',
            'deal_status', 'company', 'interviewee_name', 'date_of_interview'
        ]
        core_cols = [col for col in core_cols if col in df.columns]
        st.markdown("### Validated Quotes")
        st.dataframe(df[core_cols], use_container_width=True, height=400)
        st.caption(f"Showing {len(df)} validated quotes")

with tabs[1]:
    # Response Data Table (raw output)
    if not os.path.exists(STAGE1_CSV) or os.path.getsize(STAGE1_CSV) == 0:
        st.info("No processed data found. Upload and process files to see the response data table.")
    else:
        df = load_csv(STAGE1_CSV)
        st.markdown("### Response Data Table (Raw Output)")
        st.dataframe(df, use_container_width=True, height=400)
        st.caption(f"{len(df)} responses loaded")

with tabs[2]:
    # Prompt Template
    st.markdown("### Prompt Template (Core Extraction)")
    st.code(load_prompt_template(), language="python")

with tabs[3]:
    # Processing Details
    st.markdown("### Processing Details")
    st.markdown(PROCESSING_DETAILS)


