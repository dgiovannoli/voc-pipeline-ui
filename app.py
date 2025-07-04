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
    """Process uploaded files using the pipeline"""
    if not st.session_state.uploaded_paths:
        raise Exception("No files uploaded")
    
    # Process using original pipeline
    for path in st.session_state.uploaded_paths:
        interviewee, company = extract_interviewee_and_company(os.path.basename(path))
        subprocess.run([
            sys.executable, "-m", "voc_pipeline", "process_transcript",
            path,
            company if company else "Unknown",
            company if company else "Unknown", 
            interviewee if interviewee else "Unknown",
            "closed_won",
            "2024-01-01"
        ], check=True)

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
col1, col2, col3, col4 = st.columns(4)
with col1:
    step1_active = st.session_state.current_step >= 1
    st.markdown(f"""
    <div class="step-card {'step-active' if step1_active else ''}">
        <h3>📁 Upload</h3>
        <p>Upload interview files</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    step2_active = st.session_state.current_step >= 2
    st.markdown(f"""
    <div class="step-card {'step-active' if step2_active else ''}">
        <h3>🔍 Process</h3>
        <p>Extract responses</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    step3_active = st.session_state.current_step >= 3
    st.markdown(f"""
    <div class="step-card {'step-active' if step3_active else ''}">
        <h3>✅ Validate</h3>
        <p>Validate & enrich</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    step4_active = st.session_state.current_step >= 4
    st.markdown(f"""
    <div class="step-card {'step-active' if step4_active else ''}">
        <h3>📊 Export</h3>
        <p>Download results</p>
    </div>
    """, unsafe_allow_html=True)

# Step 1: Upload
if st.session_state.current_step == 1:
    st.markdown("## 📁 Upload Interview Files")
    
    uploads = st.file_uploader(
        "Select interview files",
        type=["txt", "docx"],
        accept_multiple_files=True,
        help="Upload .txt or .docx files containing customer interviews"
    )
    
    if uploads:
        st.success(f"✅ {len(uploads)} files uploaded")
        
        # Show uploaded files
        for i, f in enumerate(uploads):
            filename = f.name
            interviewee, company = extract_interviewee_and_company(filename)
            st.write(f"**{i+1}. {filename}**")
            if interviewee or company:
                st.write(f"   👤 {interviewee} | 🏢 {company}")
        
        if st.button("🚀 Start Processing", type="primary", use_container_width=True):
            # Save files
            st.session_state.uploaded_paths = []
            for f in uploads:
                dest = UPLOAD_DIR / f.name
                with open(dest, "wb") as out:
                    out.write(f.getbuffer())
                st.session_state.uploaded_paths.append(str(dest))
            
            st.session_state.current_step = 2
            st.rerun()

# Step 2: Process
elif st.session_state.current_step == 2:
    st.markdown("## 🔍 Processing Files")
    
    if not st.session_state.uploaded_paths:
        st.error("No files uploaded. Please go back to step 1.")
        if st.button("⬅️ Back to Upload"):
            st.session_state.current_step = 1
            st.rerun()
    else:
        # Show files being processed
        st.write("**Files to process:**")
        for path in st.session_state.uploaded_paths:
            st.write(f"• {os.path.basename(path)}")
        
        if st.button("▶️ Process Files", type="primary", use_container_width=True):
            with st.spinner("Processing files..."):
                try:
                    process_files()
                    st.success("✅ Processing complete!")
                    st.session_state.current_step = 3
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Processing failed: {e}")

# Step 3: Validate & Enrich
elif st.session_state.current_step == 3:
    st.markdown("## ✅ Validate & Enrich")
    
    if not os.path.exists(STAGE1_CSV):
        st.error("No processed data found. Please complete step 2 first.")
        if st.button("⬅️ Back to Process"):
            st.session_state.current_step = 2
            st.rerun()
    else:
        # Show processing stats
        df = load_csv(STAGE1_CSV)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Responses", len(df))
        with col2:
            st.metric("Companies", df['Company Name'].nunique() if 'Company Name' in df.columns else 0)
        with col3:
            st.metric("Subjects", df['Subject'].nunique() if 'Subject' in df.columns else 0)
        
        if st.button("✅ Validate & Enrich", type="primary", use_container_width=True):
            with st.spinner("Validating and enriching..."):
                try:
                    validate_and_build()
                    
                    # Save to database
                    if os.path.exists(RESPONSE_TABLE_CSV):
                        count = st.session_state.db.migrate_csv_to_db(str(RESPONSE_TABLE_CSV))
                        st.success(f"✅ Validation complete! Saved {count} responses to database.")
                    
                    st.session_state.current_step = 4
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Validation failed: {e}")

# Step 4: Export
elif st.session_state.current_step == 4:
    st.markdown("## 📊 Export Results")
    
    stats = st.session_state.db.get_stats()
    
    # Show final stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Responses", stats.get('total_responses', 0))
    with col2:
        st.metric("AI Analyses", stats.get('total_analyses', 0))
    with col3:
        st.metric("Companies", len(stats.get('responses_by_company', {})))
    with col4:
        st.metric("Subjects", len(stats.get('responses_by_subject', {})))
    
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
