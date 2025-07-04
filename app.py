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
    name = filename.rsplit('.', 1)[0]
    # Try to extract "Interview with [Interviewee], ... at [Company]"
    match = re.search(r'Interview with ([^,]+),.*? at ([^.,]+)', name, re.IGNORECASE)
    if match:
        interviewee = match.group(1).strip()
        company = match.group(2).strip()
        return interviewee, company
    # Try to extract "Interview with [Interviewee] at [Company]"
    match = re.search(r'Interview with ([^,]+) at ([^.,]+)', name, re.IGNORECASE)
    if match:
        interviewee = match.group(1).strip()
        company = match.group(2).strip()
        return interviewee, company
    # Try to extract "Interview with [Interviewee]"
    match = re.search(r'Interview with ([^.,-]+)', name, re.IGNORECASE)
    if match:
        interviewee = match.group(1).strip()
        return interviewee, ""
    # Fallback: use the whole name as interviewee
    return name.strip(), ""

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
    for path in st.session_state.uploaded_paths:
        interviewee, company = extract_interviewee_and_company(os.path.basename(path))
        result = subprocess.run([
            sys.executable, "-m", "voc_pipeline.modular_cli", "extract-core",
            path,
            company if company else "Unknown",
            interviewee if interviewee else "Unknown",
            "closed_won",
            "2024-01-01",
            "-o", str(STAGE1_CSV)
        ], capture_output=True, text=True)
        if result.returncode != 0:
            st.error(f"Processing failed!\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}")
            return
    if not os.path.exists(STAGE1_CSV) or os.path.getsize(STAGE1_CSV) == 0:
        st.error("Processing failed: No output was generated. Please check your input files and try again.")
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
st.markdown("""
<div class="main-header">
    <h1>🎯 VOC Pipeline</h1>
    <p>Transform customer interviews into actionable insights</p>
</div>
""", unsafe_allow_html=True)

# Progress indicator
col1, col2, col3 = st.columns(3)
with col1:
    step1_active = st.session_state.current_step == 1
    st.markdown(f"""
    <div class="step-card {'step-active' if step1_active else ''}">
        <h3>📁 Upload & Process</h3>
        <p>Upload and process files</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    step2_active = st.session_state.current_step == 2
    st.markdown(f"""
    <div class="step-card {'step-active' if step2_active else ''}">
        <h3>✅ Validate</h3>
        <p>Validate & enrich</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    step3_active = st.session_state.current_step == 3
    st.markdown(f"""
    <div class="step-card {'step-active' if step3_active else ''}">
        <h3>📊 Export</h3>
        <p>Download results</p>
    </div>
    """, unsafe_allow_html=True)

# Step 1: Upload & Process
if st.session_state.current_step == 1:
    uploads = st.file_uploader(
        "Select interview files",
        type=["txt", "docx"],
        accept_multiple_files=True,
        help="Upload .txt or .docx files containing customer interviews"
    )
    if uploads:
        # Always clear old outputs
        for f in [STAGE1_CSV, VALIDATED_CSV, RESPONSE_TABLE_CSV]:
            if os.path.exists(f):
                os.remove(f)
        st.session_state.uploaded_paths = []
        for f in uploads:
            dest = UPLOAD_DIR / f.name
            with open(dest, "wb") as out:
                out.write(f.getbuffer())
            st.session_state.uploaded_paths.append(str(dest))
        if st.button("▶️ Process Files", type="primary", use_container_width=True):
            with st.spinner("Processing files..."):
                try:
                    process_files()
                    # Check if output exists and is non-empty
                    if not (os.path.exists(STAGE1_CSV) and os.path.getsize(STAGE1_CSV) > 0):
                        st.error("Processing failed: No output was generated. Please check your input files and try again.")
                    else:
                        st.session_state.current_step = 2
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Processing failed: {e}")

# Step 2: Validate & Enrich
elif st.session_state.current_step == 2:
    st.markdown("## ✅ Validate & Enrich")
    if not os.path.exists(STAGE1_CSV):
        st.error("No processed data found. Please upload and process files first.")
        if st.button("⬅️ Back to Upload"):
            st.session_state.current_step = 1
            st.rerun()
    else:
        df = load_csv(STAGE1_CSV)
        st.markdown(f"**Available columns:** {list(df.columns)}")
        st.markdown(f"**Data shape:** {df.shape}")
        
        # Only show core columns
        core_cols = [
            'response_id', 'verbatim_response', 'subject', 'question',
            'deal_status', 'company', 'interviewee_name', 'date_of_interview'
        ]
        core_cols = [col for col in core_cols if col in df.columns]
        st.markdown(f"**Core columns found:** {core_cols}")
        
        if core_cols:
            st.markdown("### Extracted Responses (Source of Truth)")
            st.dataframe(df[core_cols], use_container_width=True, height=300)
        else:
            st.error("No core columns found in the data. Available columns: " + ", ".join(df.columns))
        # Show prompt and approach
        with st.expander("🔎 Show Prompt & Processing Approach"):
            st.markdown("**Prompt Template:**")
            st.code(CORE_EXTRACTION_PROMPT, language="text")
            st.markdown("**Approach:**\n- Validate each response for required fields and completeness.\n- Remove duplicates.\n- Enrich with missing metadata if available.\n- Prepare for downstream analysis and labeling.")
        if st.button("✅ Validate & Enrich", type="primary", use_container_width=True):
            with st.spinner("Validating and enriching..."):
                try:
                    validate_and_build()
                    if os.path.exists(RESPONSE_TABLE_CSV):
                        count = st.session_state.db.migrate_csv_to_db(str(RESPONSE_TABLE_CSV))
                    st.session_state.current_step = 3
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Validation failed: {e}")

# Step 3: Export
elif st.session_state.current_step == 3:
    st.markdown("## 📊 Export Results")
    
    stats = st.session_state.db.get_stats()
    
    # Show final stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Responses", stats.get('total_responses', 0))
    with col2:
        st.metric("AI Analyses", stats.get('total_analyses', 0))
    with col3:
        st.metric("Companies", len(stats.get('responses_by_company', {})))
    
    # Export options
    st.markdown("### 📤 Download Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Download Complete Dataset", type="primary", use_container_width=True):
            if stats.get('total_responses', 0) > 0:
                df_complete = st.session_state.db.get_responses()
                csv_data = df_complete.to_csv(index=False)
                st.download_button(
                    "Download Complete Dataset",
                    data=csv_data,
                    file_name=f"voc_complete_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data to export")
    
    with col2:
        if st.button("📥 Download Core Data", use_container_width=True):
            if stats.get('total_responses', 0) > 0:
                df_core = st.session_state.db.get_responses()
                core_cols = ['response_id', 'verbatim_response', 'subject', 'question', 'deal_status', 'company', 'interviewee_name', 'date_of_interview']
                df_core = df_core[core_cols]
                csv_data = df_core.to_csv(index=False)
                st.download_button(
                    "Download Core Data",
                    data=csv_data,
                    file_name=f"voc_core_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data to export")
    
    # Sample data preview
    if stats.get('total_responses', 0) > 0:
        st.markdown("### 📋 Sample Data")
        df_sample = st.session_state.db.get_responses()
        st.dataframe(df_sample.head(10), use_container_width=True)
    
    # Restart
    st.markdown("---")
    if st.button("🔄 Start New Pipeline", type="primary", use_container_width=True):
        st.session_state.current_step = 1
        st.session_state.uploaded_paths = []
        st.rerun()
