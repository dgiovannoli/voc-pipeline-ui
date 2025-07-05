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
import sqlite3
import yaml
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

# Supabase integration
try:
    from supabase_integration import HybridDatabaseManager
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    st.warning("⚠️ Supabase integration not available. Install with: pip install supabase")

load_dotenv()

# Debug information (commented out for production)
# st.write("Current working directory:", os.getcwd())
# st.write("voc_pipeline.db exists:", os.path.exists("voc_pipeline.db"))

# Helper functions
def extract_interviewee_and_company(filename):
    """
    Extract interviewee and company from filename.
    Example: 'Interview with Ben Evenstad, Owner at Evenstad Law.docx' -> ('Ben Evenstad', 'Evenstad Law')
    """
    base = os.path.basename(filename).replace('.docx', '').replace('.txt', '')
    
    # Handle simple filenames without interview format
    if not base.lower().startswith("interview with "):
        return ("Unknown", "Unknown")
    
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
# (Removed duplicate sidebar - now only in main() function)

# --- MAIN AREA ---
# (Removed old tabs - now using workflow-based navigation)

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

def init_database():
    """Initialize database if it doesn't exist"""
    try:
        with sqlite3.connect("voc_pipeline.db") as conn:
            cursor = conn.cursor()
            
            # Core responses table (Stage 1 output)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS core_responses (
                    response_id VARCHAR PRIMARY KEY,
                    verbatim_response TEXT,
                    subject VARCHAR,
                    question TEXT,
                    deal_status VARCHAR,
                    company VARCHAR,
                    interviewee_name VARCHAR,
                    interview_date DATE,
                    file_source VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sync_status VARCHAR DEFAULT 'local_only'
                )
            """)
            
            # Add sync_status column if it doesn't exist (for existing databases)
            try:
                cursor.execute("ALTER TABLE core_responses ADD COLUMN sync_status VARCHAR DEFAULT 'local_only'")
            except sqlite3.OperationalError:
                # Column already exists
                pass
            
            # Quote analysis table (Stage 2 output)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quote_analysis (
                    analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quote_id VARCHAR,
                    criterion VARCHAR NOT NULL,
                    score DECIMAL(3,2),
                    priority VARCHAR CHECK (priority IN ('critical', 'high', 'medium', 'low')),
                    confidence VARCHAR CHECK (confidence IN ('high', 'medium', 'low')),
                    relevance_explanation TEXT,
                    deal_weighted_score DECIMAL(3,2),
                    context_keywords TEXT,
                    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (quote_id) REFERENCES core_responses(response_id),
                    UNIQUE(quote_id, criterion)
                )
            """)

            conn.commit()
            return True
    except Exception as e:
        st.error(f"Database initialization failed: {e}")
        return False

def save_stage1_to_database(csv_path):
    """Save Stage 1 CSV output to database"""
    try:
        df = pd.read_csv(csv_path)
        
        with sqlite3.connect("voc_pipeline.db") as conn:
            cursor = conn.cursor()
            
            for _, row in df.iterrows():
                # Parse date
                interview_date = None
                if 'date_of_interview' in row and pd.notna(row['date_of_interview']):
                    try:
                        date_str = str(row['date_of_interview'])
                        if '/' in date_str:
                            interview_date = datetime.strptime(date_str, '%m/%d/%Y').date()
                        elif '-' in date_str:
                            interview_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except:
                        interview_date = None
                
                cursor.execute("""
                    INSERT OR REPLACE INTO core_responses 
                    (response_id, verbatim_response, subject, question, deal_status, 
                     company, interviewee_name, interview_date, file_source, sync_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('response_id', ''),
                    row.get('verbatim_response', ''),
                    row.get('subject', ''),
                    row.get('question', ''),
                    row.get('deal_status', ''),
                    row.get('company', ''),
                    row.get('interviewee_name', ''),
                    interview_date,
                    csv_path,
                    'local_only'
                ))
            
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Failed to save to database: {e}")
        return False

def run_stage2_analysis():
    """Run Stage 2 analysis using the database analyzer"""
    try:
        from enhanced_stage2_analyzer import DatabaseStage2Analyzer
        
        analyzer = DatabaseStage2Analyzer()
        result = analyzer.process_incremental()
        
        if result.get('status') == 'success':
            return result
        elif result.get('status') == 'no_quotes_to_process':
            return {"status": "no_quotes", "message": "No quotes to process"}
        else:
            return {"status": "error", "message": str(result)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_stage2_summary():
    """Get summary statistics from Stage 2 analysis"""
    try:
        with sqlite3.connect("voc_pipeline.db") as conn:
            cursor = conn.cursor()
            
            # Get total quotes
            cursor.execute("SELECT COUNT(*) FROM core_responses")
            total_quotes = cursor.fetchone()[0]
            
            # Get quotes with scores
            cursor.execute("SELECT COUNT(DISTINCT quote_id) FROM quote_analysis")
            quotes_with_scores = cursor.fetchone()[0]
            
            # Get criteria performance
            cursor.execute("""
                SELECT criterion, 
                       COUNT(*) as mention_count,
                       AVG(deal_weighted_score) as avg_score
                FROM quote_analysis 
                GROUP BY criterion
                ORDER BY avg_score DESC
            """)
            criteria_performance = {}
            for row in cursor.fetchall():
                criterion, mentions, avg_score = row
                criteria_performance[criterion] = {
                    "mention_count": mentions,
                    "average_score": round(avg_score, 2),
                    "coverage_percentage": round((mentions / total_quotes) * 100, 1) if total_quotes > 0 else 0
                }
            
            return {
                "total_quotes": total_quotes,
                "quotes_with_scores": quotes_with_scores,
                "coverage_percentage": round((quotes_with_scores / total_quotes) * 100, 1) if total_quotes > 0 else 0,
                "criteria_performance": criteria_performance
            }
    except Exception as e:
        return None


def show_supabase_sync():
    """Show Supabase sync section"""
    st.title("☁️ Supabase Sync")
    st.markdown("Sync your local data to Supabase for cloud sharing and collaboration")
    
    if not SUPABASE_AVAILABLE:
        st.error("❌ Supabase integration not available. Please install with: `pip install supabase`")
        return
    
    # Initialize hybrid database manager
    try:
        db_manager = HybridDatabaseManager()
        st.success("✅ Hybrid database manager initialized")
    except Exception as e:
        st.error(f"❌ Failed to initialize database manager: {e}")
        return
    
    # Show sync status
    st.subheader("📊 Sync Status")
    
    try:
        status = db_manager.get_sync_status()
        
        if "error" in status:
            st.error(f"❌ Error getting sync status: {status['error']}")
            return
        
        # Display status metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Supabase Available", 
                "✅ Yes" if status.get('supabase_available') else "❌ No"
            )
        
        with col2:
            local_responses = status.get('total_local_responses', 0)
            synced_responses = status.get('core_responses', {}).get('synced', 0)
            st.metric("Local Responses", local_responses)
        
        with col3:
            local_analyses = status.get('total_local_analyses', 0)
            synced_analyses = status.get('quote_analysis', {}).get('synced', 0)
            st.metric("Local Analyses", local_analyses)
        
        # Show detailed sync status
        st.markdown("---")
        st.subheader("🔍 Detailed Sync Status")
        
        # Core responses sync status
        response_status = status.get('core_responses', {})
        if response_status:
            st.write("**Core Responses:**")
            for sync_type, count in response_status.items():
                st.write(f"  - {sync_type}: {count}")
        
        # Quote analysis sync status
        analysis_status = status.get('quote_analysis', {})
        if analysis_status:
            st.write("**Quote Analysis:**")
            for sync_type, count in analysis_status.items():
                st.write(f"  - {sync_type}: {count}")
                
    except Exception as e:
        st.error(f"❌ Error getting sync status: {e}")
        return
    
    # Sync actions
        st.markdown("---")
        st.subheader("🔄 Sync Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Sync All to Supabase", key="sync_all", use_container_width=True):
                with st.spinner("Syncing data to Supabase..."):
                    try:
                        sync_stats = db_manager.sync_all_to_supabase()
                        
                        if "error" in sync_stats:
                            st.error(f"❌ Sync failed: {sync_stats['error']}")
                        else:
                            st.success(f"✅ Sync completed!")
                            st.write(f"**Synced:**")
                            st.write(f"  - Core responses: {sync_stats.get('core_responses', 0)}")
                            st.write(f"  - Quote analyses: {sync_stats.get('quote_analysis', 0)}")
                            st.write(f"  - Errors: {sync_stats.get('errors', 0)}")
                            
                            # Refresh the page to update status
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Sync error: {e}")
        
        with col2:
            if st.button("🔄 Refresh Status", key="refresh_status", use_container_width=True):
                st.rerun()
        
        # Manual sync options
        st.markdown("---")
        st.subheader("⚙️ Manual Sync Options")
        
        if st.button("📊 Test Supabase Connection", key="test_connection", use_container_width=True):
            with st.spinner("Testing connection..."):
                try:
                    # Try to get a small amount of data from Supabase
                    test_df = db_manager.get_data_for_sharing()
                    if not test_df.empty:
                        st.success("✅ Supabase connection successful!")
                        st.write(f"Retrieved {len(test_df)} records from Supabase")
                    else:
                        st.info("ℹ️ Supabase connection successful, but no data found")
                except Exception as e:
                    st.error(f"❌ Supabase connection failed: {e}")
        
        # Show sync configuration
        st.markdown("---")
        st.subheader("⚙️ Sync Configuration")
        
        st.info("""
        **Sync Strategy:** One-way sync (Local → Cloud)
        
        **Sync Triggers:**
        - Manual sync button (above)
        - After processing new data
        - Scheduled sync (coming soon)
        
        **Data Flow:**
        1. Process data locally (fast)
        2. Sync to Supabase for sharing
        3. Keep local as source of truth
        4. Fallback to local if cloud unavailable
        """)
        
        # Environment variables status
        st.markdown("**Environment Variables:**")
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if supabase_url:
            st.success(f"✅ SUPABASE_URL: {supabase_url[:30]}...")
        else:
            st.error("❌ SUPABASE_URL not set")
        
        if supabase_key:
            st.success(f"✅ SUPABASE_ANON_KEY: {supabase_key[:20]}...")
        else:
            st.error("❌ SUPABASE_ANON_KEY not set")


def main():
    
    # Initialize database
    if not init_database():
        st.error("Failed to initialize database")
        return
    
    # Initialize session state
    if 'current_step' not in st.session_state:
        st.session_state.current_step = None
    if 'progress' not in st.session_state:
        st.session_state.progress = 0.0
    
    # Progress bar placeholder
    global progress_placeholder
    progress_placeholder = st.empty()
    progress_placeholder.progress(st.session_state.progress, text="Idle")
    
    # Sidebar
    with st.sidebar:
        st.title("🎤 VOC Pipeline")
        st.markdown("---")
        
        # Workflow steps
        st.subheader("Workflow")
        
        # Step 1: Upload & Process
        if st.button("📁 Upload & Process", use_container_width=True, key="main_upload"):
            st.session_state.current_step = "upload"
        
        # Step 2: Stage 1 Results
        if st.button("📊 Stage 1 Results", use_container_width=True, key="main_stage1"):
            st.session_state.current_step = "stage1"
        
        # Step 3: Stage 2 Analysis
        if st.button("🎯 Stage 2 Analysis", use_container_width=True, key="main_stage2"):
            st.session_state.current_step = "stage2"
        
        # Step 4: Export
        if st.button("💾 Export Data", use_container_width=True, key="main_export"):
            st.session_state.current_step = "export"
        
        # Step 5: Prompts & Details
        if st.button("📝 Prompts & Details", use_container_width=True, key="main_prompts"):
            st.session_state.current_step = "prompts"
        
        # Step 6: Supabase Sync (if available)
        if SUPABASE_AVAILABLE:
            if st.button("☁️ Supabase Sync", use_container_width=True, key="main_sync"):
                st.session_state.current_step = "sync"
        
        st.markdown("---")
    
    # Main content area
    if st.session_state.get('current_step') == "upload":
        show_upload_section()
    elif st.session_state.get('current_step') == "stage1":
        show_stage1_results()
    elif st.session_state.get('current_step') == "stage2":
        show_stage2_analysis()
    elif st.session_state.get('current_step') == "export":
        show_export_section()
    elif st.session_state.get('current_step') == "prompts":
        show_prompts_details()
    elif st.session_state.get('current_step') == "sync":
        show_supabase_sync()
    else:
        show_welcome_screen()

def show_upload_section():
    st.title("📁 Upload & Process Interviews")
    st.markdown("Upload interview transcript files and extract core responses")
    
    # File uploader
    uploads = st.file_uploader(
        "Select .txt or .docx files", 
        type=["txt", "docx"], 
        accept_multiple_files=True,
        key="file_uploader"
    )
    
    if uploads:
        # Save uploaded files
        uploaded_paths = save_uploaded_files(uploads)
        st.success(f"✅ {len(uploads)} files uploaded successfully")
        
        # Show uploaded files
        st.subheader("📋 Uploaded Files")
        for i, path in enumerate(uploaded_paths):
            filename = os.path.basename(path)
            interviewee, company = extract_interviewee_and_company(filename)
            st.write(f"**{i+1}.** {filename}")
            if company or interviewee:
                st.caption(f"Company: {company or 'Unknown'} | Interviewee: {interviewee or 'Unknown'}")
        
        # Process files button
        if st.button("🚀 Process Files", key="upload_process_files", use_container_width=True):
            if uploaded_paths:
                with st.spinner("Processing files..."):
                    try:
                        # Store paths in session state for processing
                        st.session_state.uploaded_paths = uploaded_paths
                        
                        # Process files
                        process_files_with_progress()
                        
                        st.success("✅ Files processed successfully!")
                        st.info("Go to '📊 Stage 1 Results' to view extracted quotes")
                        
                    except Exception as e:
                        st.error(f"❌ Processing failed: {e}")
            else:
                st.error("No files to process")
    else:
        st.info("👆 Upload interview transcript files (.txt or .docx) to get started")
        
        # Show example of expected format
        with st.expander("📖 Expected File Format"):
            st.markdown("""
            **Supported formats:**
            - `.txt` - Plain text interview transcripts
            - `.docx` - Word documents with interview content
            
            **Expected content:**
            - Interview transcripts with Q&A format
            - Speaker identification (optional)
            - Natural conversation flow
            
            **Example:**
            ```
            Interviewer: How has your firm utilized Rev for AI compliance?
            Christina: When I use Rev, it was for our AI and managing different meetings...
            ```
            """)

def show_stage1_results():
    """Show Stage 1 results section"""
    st.title("📊 Stage 1: Core Extraction Results")
    st.markdown("View extracted quotes and responses from interview transcripts")
    
    # Check if we have Stage 1 data
    if not os.path.exists(STAGE1_CSV) or os.path.getsize(STAGE1_CSV) == 0:
        st.warning("No Stage 1 data found. Please upload and process files first.")
        return
    
    # Load and display data
    df = load_csv(STAGE1_CSV)
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Responses", len(df))
    with col2:
        st.metric("Companies", df['company'].nunique() if 'company' in df.columns else 0)
    with col3:
        st.metric("Interviewees", df['interviewee_name'].nunique() if 'interviewee_name' in df.columns else 0)
    
    # Display data
    st.markdown("---")
    st.subheader("📋 Extracted Responses")
    
    # Core columns to display
    core_cols = [
        'response_id', 'verbatim_response', 'subject', 'question',
        'deal_status', 'company', 'interviewee_name', 'date_of_interview'
    ]
    display_cols = [col for col in core_cols if col in df.columns]
    
    st.dataframe(df[display_cols], use_container_width=True, height=400)
    
    # Download option
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Stage 1 Results (CSV)",
        data=csv,
        file_name="stage1_results.csv",
        mime="text/csv",
        key="download_stage1"
    )

def show_stage2_analysis():
    """Show Stage 2 analysis section"""
    st.title("🎯 Stage 2: Quote Analysis")
    st.markdown("Analyze extracted quotes against the 10-criteria executive framework")
    
    # Check if we have Stage 1 data
    if not os.path.exists(STAGE1_CSV):
        st.warning("No Stage 1 data found. Please run Stage 1 extraction first.")
        return
    
    # Save Stage 1 data to database if not already there
    if st.button("💾 Save Stage 1 to Database", key="stage2_save_to_db"):
        with st.spinner("Saving Stage 1 data to database..."):
            if save_stage1_to_database(STAGE1_CSV):
                st.success("Stage 1 data saved to database!")
            else:
                st.error("Failed to save Stage 1 data")
    
    # Run Stage 2 analysis
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🚀 Run Stage 2 Analysis", use_container_width=True, key="stage2_run_analysis"):
            with st.spinner("Running Stage 2 analysis..."):
                result = run_stage2_analysis()
                
                if result.get('status') == 'success':
                    st.success("Stage 2 analysis completed!")
                    st.session_state.stage2_result = result
                    
                    # Auto-sync to Supabase if available
                    if SUPABASE_AVAILABLE:
                        try:
                            db_manager = HybridDatabaseManager()
                            sync_stats = db_manager.sync_all_to_supabase()
                            if "error" not in sync_stats:
                                st.success(f"☁️ Auto-synced {sync_stats.get('core_responses', 0)} responses to Supabase")
                            else:
                                st.warning(f"⚠️ Auto-sync failed: {sync_stats['error']}")
                        except Exception as e:
                            st.warning(f"⚠️ Auto-sync failed: {e}")
                elif result.get('status') == 'no_quotes':
                    st.info("No quotes to process - all quotes already analyzed")
                else:
                    st.error(f"Stage 2 analysis failed: {result.get('message')}")
    
    with col2:
        if st.button("🔄 Force Reprocess All", use_container_width=True, key="stage2_force_reprocess"):
            with st.spinner("Force reprocessing all quotes..."):
                try:
                    from enhanced_stage2_analyzer import DatabaseStage2Analyzer
                    analyzer = DatabaseStage2Analyzer()
                    result = analyzer.process_incremental(force_reprocess=True)
                    if result.get('status') == 'success':
                        st.success("Force reprocess completed!")
                        st.session_state.stage2_result = result
                    else:
                        st.error(f"Force reprocess failed: {result}")
                except Exception as e:
                    st.error(f"Force reprocess failed: {e}")
    
    # Show Stage 2 results
    if st.session_state.get('stage2_result'):
        result = st.session_state.stage2_result
        st.markdown("---")
        st.subheader("📊 Stage 2 Results")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Quotes Processed", result.get('quotes_processed', 0))
        with col2:
            st.metric("Quotes Analyzed", result.get('quotes_analyzed', 0))
        with col3:
            st.metric("Processing Time", f"{result.get('processing_duration_seconds', 0):.1f}s")
        with col4:
            st.metric("Success Rate", f"{(result.get('quotes_analyzed', 0) / result.get('quotes_processed', 1) * 100):.1f}%")
    
    # Show summary statistics
    summary = get_stage2_summary()
    if summary:
        st.markdown("---")
        st.subheader("📈 Analysis Summary")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Quotes", summary['total_quotes'])
            st.metric("Quotes with Scores", summary['quotes_with_scores'])
            st.metric("Coverage", f"{summary['coverage_percentage']}%")
        
        with col2:
            # Top performing criteria
            st.subheader("🏆 Top Performing Criteria")
            sorted_criteria = sorted(
                summary['criteria_performance'].items(),
                key=lambda x: x[1]['average_score'],
                reverse=True
            )[:5]
            
            for criterion, perf in sorted_criteria:
                st.metric(
                    criterion.replace('_', ' ').title(),
                    f"{perf['average_score']:.2f}",
                    f"{perf['mention_count']} mentions"
                )
        
        # Criteria performance chart
        if summary['criteria_performance']:
            st.markdown("---")
            st.subheader("📊 Criteria Performance")
            
            criteria_data = []
            for criterion, perf in summary['criteria_performance'].items():
                criteria_data.append({
                    'Criterion': criterion.replace('_', ' ').title(),
                    'Average Score': perf['average_score'],
                    'Mentions': perf['mention_count'],
                    'Coverage %': perf['coverage_percentage']
                })
            
            df_criteria = pd.DataFrame(criteria_data)
            st.dataframe(df_criteria, use_container_width=True)
    
    # Show raw analysis data
    if st.checkbox("🔍 Show Raw Analysis Data"):
        try:
            with sqlite3.connect("voc_pipeline.db") as conn:
                query = """
                SELECT qa.quote_id, qa.criterion, qa.score, qa.deal_weighted_score,
                       qa.priority, qa.confidence, qa.relevance_explanation,
                       cr.company, cr.interviewee_name, cr.deal_status
                FROM quote_analysis qa
                JOIN core_responses cr ON qa.quote_id = cr.response_id
                ORDER BY qa.analysis_timestamp DESC
                LIMIT 1000
                """
                df_analysis = pd.read_sql_query(query, conn)

            # Only show criteria with score > 0 (default to 1 to hide zero scores)
            min_score = st.slider("Minimum Score to Display", 0, 5, 1, 1, help="Show only criteria with at least this score (0=show all, 1=hide zero scores)")
            df_analysis = df_analysis[df_analysis['score'] >= min_score]

            # Sort options
            sort_col = st.selectbox("Sort by", ["score", "criterion", "priority", "confidence"], index=0)
            sort_ascending = st.radio("Sort order", ["Descending", "Ascending"], index=0) == "Ascending"
            df_analysis = df_analysis.sort_values(by=sort_col, ascending=sort_ascending)

            # Color map for score
            def score_color(val):
                if val == 1:
                    return 'background-color: #e0e0e0; color: #333;'  # gray
                elif val == 2:
                    return 'background-color: #b3c6ff; color: #222;'  # blue
                elif val == 3:
                    return 'background-color: #b6f5b6; color: #222;'  # green
                elif val == 4:
                    return 'background-color: #ffd580; color: #222;'  # orange
                elif val == 5:
                    return 'background-color: #ff9999; color: #222;'  # red
                else:
                    return ''

            # Custom column configs for tooltips (Streamlit 1.25+)
            column_config = {
                "score": st.column_config.NumberColumn(
                    "Score (1–5)",
                    help="Intensity of feedback (1=slight, 5=exceptional)",
                    format="%d"
                ),
                "relevance_explanation": st.column_config.TextColumn(
                    "Relevance Explanation",
                    help="Explanation of how this quote relates to the criterion"
                )
            }

            # Display table with color and tooltips
            styled_df = df_analysis.style.applymap(score_color, subset=["score"])
            st.dataframe(
                df_analysis,
                use_container_width=True,
                column_config=column_config,
                hide_index=True
            )
            st.caption("Scores are color-coded: 1=gray, 2=blue, 3=green, 4=orange, 5=red. Hover for explanations.")
        except Exception as e:
            st.error(f"Failed to load analysis data: {e}")

def show_export_section():
    """Show export section"""
    st.title("💾 Export Data")
    st.markdown("Export processed data in various formats")
    
    # Stage 1 export
    if os.path.exists(STAGE1_CSV) and os.path.getsize(STAGE1_CSV) > 0:
        st.subheader("📊 Stage 1 Results")
        df_stage1 = load_csv(STAGE1_CSV)
        
        col1, col2 = st.columns(2)
        with col1:
            csv_stage1 = df_stage1.to_csv(index=False)
            st.download_button(
                label="📥 Download Stage 1 (CSV)",
                data=csv_stage1,
                file_name="stage1_results.csv",
                mime="text/csv",
                key="export_stage1_csv"
            )
        
        with col2:
            # Export as JSON
            json_stage1 = df_stage1.to_json(orient='records', indent=2)
            st.download_button(
                label="📥 Download Stage 1 (JSON)",
                data=json_stage1,
                file_name="stage1_results.json",
                mime="application/json",
                key="export_stage1_json"
            )
    
    # Stage 2 export
    try:
        with sqlite3.connect("voc_pipeline.db") as conn:
            # Check if we have Stage 2 data
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM quote_analysis")
            stage2_count = cursor.fetchone()[0]
            
            if stage2_count > 0:
                st.subheader("🎯 Stage 2 Analysis Results")
                
                # Export analysis data
                query = """
                SELECT qa.quote_id, qa.criterion, qa.score, qa.deal_weighted_score,
                       qa.priority, qa.confidence, qa.relevance_explanation,
                       cr.company, cr.interviewee_name, cr.deal_status,
                       qa.analysis_timestamp
                FROM quote_analysis qa
                JOIN core_responses cr ON qa.quote_id = cr.response_id
                ORDER BY qa.analysis_timestamp DESC
                """
                df_stage2 = pd.read_sql_query(query, conn)
                
                col1, col2 = st.columns(2)
                with col1:
                    csv_stage2 = df_stage2.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Stage 2 (CSV)",
                        data=csv_stage2,
                        file_name="stage2_analysis.csv",
                        mime="text/csv",
                        key="export_stage2_csv"
                    )
                
                with col2:
                    json_stage2 = df_stage2.to_json(orient='records', indent=2)
                    st.download_button(
                        label="📥 Download Stage 2 (JSON)",
                        data=json_stage2,
                        file_name="stage2_analysis.json",
                        mime="application/json",
                        key="export_stage2_json"
                    )
                
                # Export summary
                summary = get_stage2_summary()
                if summary:
                    st.markdown("---")
                    st.subheader("📈 Summary Report")
                    
                    summary_json = json.dumps(summary, indent=2)
                    st.download_button(
                        label="📥 Download Summary Report (JSON)",
                        data=summary_json,
                        file_name="analysis_summary.json",
                        mime="application/json",
                        key="export_summary"
                    )
            else:
                st.info("No Stage 2 analysis data available. Run Stage 2 analysis first.")
    except Exception as e:
        st.error(f"Failed to access database: {e}")

def show_prompts_details():
    """Show prompts and processing details"""
    st.title("📝 Prompts & Processing Details")
    st.markdown("View the AI prompts and processing details for each stage of the pipeline")
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Stage 1", "🎯 Stage 2", "📊 Processing", "🗄️ Database", "⚙️ Config"])
    
    with tab1:
        st.subheader("🎯 Stage 1: Core Extraction Prompt")
        st.markdown("This prompt extracts essential verbatim responses from interview transcripts.")
        
        # Load and display the core extraction prompt
        try:
            from prompts.core_extraction import CORE_EXTRACTION_PROMPT
            with st.expander("📝 View Full Prompt", expanded=False):
                st.code(CORE_EXTRACTION_PROMPT, language="text")
        except ImportError:
            st.error("Could not load core extraction prompt")
        
        st.markdown("---")
        st.subheader("Stage 1 Processing Details")
        st.markdown("""
        **What Stage 1 Does:**
        - Processes interview transcript files (.txt, .docx)
        - Uses intelligent chunking to break large files into manageable segments
        - Extracts 3-5 richest, most detailed responses per chunk
        - Preserves complete verbatim responses with full context
        - Generates structured metadata (subject, question, company, interviewee)
        
        **Key Features:**
        - **Quality-focused extraction**: Prioritizes comprehensive responses with specific examples
        - **Context preservation**: Maintains full conversation flow and context
        - **Deduplication**: Removes duplicate or similar responses
        - **Metadata generation**: Automatically extracts company, interviewee, and subject information
        """)
    
    with tab2:
        st.subheader("🎯 Stage 2: Quote Analysis Prompt")
        st.markdown("This prompt analyzes extracted quotes against the 10-criteria executive framework using Binary + Intensity scoring.")
        
        # Display the Stage 2 prompt (from the analyzer)
        stage2_prompt = """
ANALYZE THIS QUOTE against the 10-criteria executive framework using BINARY + INTENSITY scoring.

DEAL CONTEXT: {deal_status} deal

QUOTE TO ANALYZE:
Subject: {subject}
Question: {question}
Response: {verbatim_response}

EVALUATION CRITERIA:
- product_capability: Functionality, features, performance, and core solution fit
- implementation_onboarding: Deployment ease, time-to-value, setup complexity
- integration_technical_fit: APIs, data compatibility, technical architecture alignment
- support_service_quality: Post-sale support, responsiveness, expertise, SLAs
- security_compliance: Data protection, certifications, governance, risk management
- market_position_reputation: Brand trust, references, analyst recognition, market presence
- vendor_stability: Financial health, roadmap clarity, long-term viability
- sales_experience_partnership: Buying process quality, relationship building, trust
- commercial_terms: Price, contract flexibility, ROI, total cost of ownership
- speed_responsiveness: Implementation timeline, decision-making speed, agility

BINARY + INTENSITY SCORING SYSTEM:
- 0 = Not relevant/not mentioned (omit from scores)
- 1 = Slight mention/indirect relevance
- 2 = Clear mention/direct relevance
- 3 = Strong emphasis/important feedback
- 4 = Critical feedback/deal-breaking issue
- 5 = Exceptional praise/deal-winning strength

TASK: Score this quote against ANY criteria that are even loosely relevant. Use the binary + intensity approach:
1. First decide: Is this criterion relevant to the quote or question? (Binary: 0 or 1+)
2. If relevant, then assess intensity: How important/impactful is this feedback? (1-5)
3. Final score = Binary × Intensity (0 or 1-5)

OUTPUT FORMAT (JSON only):
{
    "scores": {
        "criterion_name": score_number
    },
    "priorities": {
        "criterion_name": "critical|high|medium|low"
    },
    "confidence": {
        "criterion_name": "high|medium|low"
    },
    "relevance_explanation": {
        "criterion_name": "Brief explanation of how this quote relates to the criterion"
    },
    "context_assessment": {
        "criterion_name": "deal_breaking|minor|neutral"
    },
    "question_relevance": {
        "criterion_name": "direct|indirect|unrelated"
    }
}

IMPORTANT: Only include criteria in "scores" that are relevant (score > 0). If a criterion is not mentioned or relevant, omit it entirely.
"""
        with st.expander("📝 View Full Prompt", expanded=False):
            st.code(stage2_prompt, language="text")
        
        st.markdown("---")
        st.subheader("Stage 2 Processing Details")
        st.markdown("""
        **What Stage 2 Does:**
        - Analyzes each quote against 10 executive criteria
        - Uses Binary + Intensity scoring (0 = not relevant, 1-5 = relevant with increasing importance)
        - Applies smart deal weighting based on deal status and context
        - Generates relevance explanations and confidence scores
        - Stores results in database for analysis
        
        **Scoring System:**
        - **0**: Not relevant/not mentioned
        - **1**: Slight mention/indirect relevance
        - **2**: Clear mention/direct relevance
        - **3**: Strong emphasis/important feedback
        - **4**: Critical feedback/deal-breaking issue
        - **5**: Exceptional praise/deal-winning strength
        
        **Deal Weighting:**
        - Lost deals: 1.2x multiplier (negative feedback more important)
        - Won deals: 0.9x multiplier (positive feedback slightly less critical)
        - Critical issues: 1.5x multiplier
        - Minor feedback: 0.7x multiplier
        """)
    
    with tab3:
        st.subheader("📊 Processing Details")
        with st.expander("📋 View Full Processing Details", expanded=False):
            st.markdown(PROCESSING_DETAILS)
        
        st.markdown("---")
        st.subheader("Additional Processing Features")
        st.markdown("""
        **Database Integration:**
        - SQLite database for persistent storage
        - Incremental processing (only new quotes)
        - Metadata storage for processing history
        
        **Quality Assurance:**
        - Deduplication at multiple stages
        - Validation of extracted responses
        - Confidence scoring for analysis
        - Error tracking and logging
        
        **Performance Optimization:**
        - Parallel processing with configurable workers
        - Token-based chunking for optimal context
        - Caching for repeated operations
        - Incremental updates to avoid reprocessing
        """)
    
    with tab4:
        st.subheader("🗄️ Database Workflow")
        st.markdown("How users interact with the database through the Streamlit interface.")
        
        st.markdown("### 📥 **Data Flow: Upload → Process → Store**")
        st.markdown("""
        1. **File Upload** (Streamlit Interface)
           - User uploads transcript files (.txt, .docx)
           - Files temporarily stored in `uploads/` directory
           - Streamlit validates file types and sizes
        
        2. **Stage 1 Processing** (Pipeline → Database)
           - Pipeline processes files and extracts quotes
           - Results automatically saved to `core_responses` table
           - Each quote gets unique `response_id` and metadata
           - Database stores: verbatim_response, subject, question, company, interviewee, deal_status
        
        3. **Stage 2 Analysis** (AI → Database)
           - AI analyzes quotes against 10 criteria
           - Results saved to `quote_analysis` table
           - Each analysis includes: scores, priorities, confidence, explanations
           - Deal-weighted scores calculated and stored
        """)
        
        st.markdown("### 🔄 **Incremental Processing**")
        st.markdown("""
        **Smart Processing Logic:**
        - **First Run**: Processes all quotes in database
        - **Subsequent Runs**: Only processes new/unanalyzed quotes
        - **Force Reprocess**: Option to re-analyze all quotes (e.g., after prompt changes)
        
        **How It Works:**
        ```sql
        SELECT cr.* FROM core_responses cr
        LEFT JOIN quote_analysis qa ON cr.response_id = qa.quote_id
        WHERE qa.analysis_id IS NULL
        ```
        """)
        
        st.markdown("### 📊 **Database Schema**")
        st.markdown("""
        **Core Tables:**
        
        **`core_responses`** (Stage 1 Output)
        - `response_id` (Primary Key)
        - `verbatim_response`, `subject`, `question`
        - `deal_status`, `company`, `interviewee_name`
        - `interview_date`, `file_source`, `created_at`
        
        **`quote_analysis`** (Stage 2 Output)
        - `analysis_id` (Primary Key)
        - `quote_id` (Foreign Key to core_responses)
        - `criterion`, `score`, `priority`, `confidence`
        - `relevance_explanation`, `deal_weighted_score`
        - `context_keywords`, `question_relevance`

        
        **`processing_metadata`** (System Tracking)
        - `metadata_id`, `processing_date`
        - `quotes_processed`, `quotes_with_scores`
        - `processing_errors`, `config_version`
        """)
        
        st.markdown("### 🖥️ **User Interface Integration**")
        st.markdown("""
        **Streamlit → Database Connections:**
        
        1. **Direct SQLite Connections** (Most Common)
           ```python
           with sqlite3.connect("voc_pipeline.db") as conn:
               cursor = conn.cursor()
               # Execute queries
               conn.commit()
           ```
        
        2. **VOCDatabase Class Wrapper**
           ```python
           from database import VOCDatabase
           st.session_state.db = VOCDatabase()
           ```
        
        3. **DatabaseStage2Analyzer Class**
           ```python
           from enhanced_stage2_analyzer import DatabaseStage2Analyzer
           analyzer = DatabaseStage2Analyzer()
           ```
        
        **UI Operations:**
        - **View Results**: Queries database for display
        - **Filter Data**: SQL WHERE clauses for company, date, criteria
        - **Export Data**: Converts database results to CSV/JSON
        - **Summary Stats**: Aggregates data for metrics display
        """)
        
        st.markdown("### 🔍 **Common User Workflows**")
        st.markdown("""
        **Workflow 1: New Data Processing**
        1. Upload transcript files via Streamlit
        2. Run Stage 1 → Data saved to `core_responses`
        3. Run Stage 2 → Analysis saved to `quote_analysis`
        4. View results in Streamlit interface
        
        **Workflow 2: Incremental Analysis**
        1. Upload new files
        2. Run Stage 1 → New quotes added to database
        3. Run Stage 2 → Only new quotes analyzed (faster)
        4. View updated results
        
        **Workflow 3: Data Exploration**
        1. Use Streamlit filters to explore specific companies/criteria
        2. View raw analysis data with color-coded scores
        3. Export filtered results for external analysis
        4. Review summary statistics
        
        **Workflow 4: Configuration Changes**
        1. Modify prompts or scoring weights
        2. Force reprocess all quotes with new settings
        3. Compare results with previous analysis
        4. Export comparison data
        """)
        
        st.markdown("### 🛡️ **Database Safety Features**")
        st.markdown("""
        **Connection Management:**
        - Automatic connection cleanup with `with` statements
        - Transaction handling for data integrity
        - Error handling and logging
        
        **Data Protection:**
        - Foreign key constraints maintain referential integrity
        - Unique constraints prevent duplicate entries
        - Check constraints validate data types
        
        **Performance:**
        - Database indexes on frequently queried columns
        - Efficient query patterns for large datasets
        - Connection pooling through class instances
        """)
    
    with tab5:
        st.subheader("⚙️ Configuration")
        st.markdown("Current system configuration and settings.")
        
        # Display current configuration
        config_info = {
            "Model": "GPT-3.5-turbo-16k",
            "Max Tokens": "4000",
            "Temperature": "0.3",
            "Max Workers": "4",
            "Max Quote Length": "1000 characters",
            "Retry Attempts": "3",
            "Batch Size": "50"
        }
        
        for key, value in config_info.items():
            st.metric(key, value)
        
        st.markdown("---")
        st.subheader("Deal Weighting Configuration")
        st.markdown("""
        **Base Weights:**
        - Lost deals: 1.2x (emphasizes negative feedback)
        - Won deals: 0.9x (reduces positive feedback importance)
        - Unknown deals: 1.0x (no adjustment)
        
        **Context Multipliers:**
        - Critical/Deal-breaking: 1.5x
        - Minor feedback: 0.7x
        - Neutral feedback: 1.0x
        """)
        
        st.markdown("---")
        st.subheader("Criteria Weights")
        st.markdown("""
        All 10 criteria currently have equal weight (1.0) and priority threshold (0.8):
        - product_capability
        - implementation_onboarding
        - integration_technical_fit
        - support_service_quality
        - security_compliance
        - market_position_reputation
        - vendor_stability
        - sales_experience_partnership
        - commercial_terms
        - speed_responsiveness
        """)

def show_welcome_screen():
    """Show welcome screen"""
    st.title("🎤 VOC Pipeline - Voice of Customer Analysis")
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Welcome to the VOC Pipeline!
        
        This tool helps you extract, analyze, and visualize insights from customer interview transcripts.
        
        **Workflow:**
        1. **📁 Upload & Process** - Upload interview transcripts and extract core responses
        2. **📊 Stage 1 Results** - View extracted quotes and validate data quality
        3. **🎯 Stage 2 Analysis** - Analyze quotes against 10-criteria executive framework

        5. **💾 Export Data** - Download results in various formats
        
        **Features:**
        - 🔍 Intelligent quote extraction with deduplication
        - 🎯 Multi-criteria analysis with deal weighting

        - 💾 Database storage for incremental processing
        - 📈 Interactive visualizations and insights
        """)
    
    with col2:
        st.markdown("""
        ### Quick Start
        
        1. Click **📁 Upload & Process** in the sidebar
        2. Upload your interview transcript files (.txt or .docx)
        3. Process the files to extract core responses
        4. View results and run Stage 2 analysis
        5. Export insights for further analysis
        
        ### Supported Formats
        - **Input:** .txt, .docx files
        - **Output:** CSV, JSON, Database
        """)
    
    # Show recent activity if available
    try:
        with sqlite3.connect("voc_pipeline.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM core_responses")
            total_quotes = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM quote_analysis")
            analyzed_quotes = cursor.fetchone()[0]
            
            if total_quotes > 0:
                st.markdown("---")
                st.subheader("📊 Recent Activity")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Quotes", total_quotes)
                with col2:
                    st.metric("Analyzed Quotes", analyzed_quotes)
    except Exception as e:
        # Database might not exist yet, which is fine
        pass

if __name__ == "__main__":
    main()


