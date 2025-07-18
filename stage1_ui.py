import streamlit as st
import os
import sys
import subprocess
import pathlib
import pandas as pd
from datetime import datetime
from supabase_database import SupabaseDatabase
from dotenv import load_dotenv
import concurrent.futures
import threading
from typing import List, Tuple, Dict

# Load environment variables
load_dotenv()

# Initialize Supabase database
try:
    db = SupabaseDatabase()
    SUPABASE_AVAILABLE = True
except Exception as e:
    SUPABASE_AVAILABLE = False
    st.error(f"❌ Failed to connect to Supabase: {e}")

# Constants
BASE = pathlib.Path(__file__).parent
STAGE1_CSV = BASE / "stage1_output.csv"

# Thread-safe progress tracking
progress_lock = threading.Lock()
progress_data = {"completed": 0, "total": 0, "results": [], "errors": []}

def extract_interviewee_and_company(filename):
    """Extract interviewee and company from filename."""
    import re
    base = os.path.basename(filename).replace('.docx', '').replace('.txt', '')
    
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
    """Save uploaded Streamlit files to disk and return a list of file paths."""
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    saved_paths = []
    for uploaded_file in uploaded_files:
        file_path = os.path.join(upload_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        saved_paths.append(file_path)
    return saved_paths

def get_client_id():
    """Safely get client_id from session state."""
    client_id = st.session_state.get('client_id', '')
    if not client_id or client_id == 'default':
        st.error("❌ **Client ID Required**")
        st.info("Please set a client ID in the sidebar before proceeding.")
        st.stop()
    return client_id

def process_single_file(file_info: Tuple[int, str]) -> Dict:
    """Process a single file and return results"""
    global progress_data
    
    file_index, file_path = file_info
    filename = os.path.basename(file_path)
    
    try:
        interviewee, company = extract_interviewee_and_company(filename)
        temp_output = BASE / f"temp_output_{file_index}.csv"
        
        # Run the extraction process
        result = subprocess.run([
            sys.executable, "-m", "voc_pipeline.modular_cli", "extract-core",
            file_path, company, interviewee, "closed_won", "2024-01-01", "-o", str(temp_output)
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        if result.returncode == 0 and temp_output.exists():
            try:
                df_temp = pd.read_csv(temp_output)
                file_result = {
                    'success': True,
                    'filename': filename,
                    'quotes_count': len(df_temp),
                    'data': df_temp,
                    'error': None
                }
            except Exception as e:
                file_result = {
                    'success': False,
                    'filename': filename,
                    'quotes_count': 0,
                    'data': None,
                    'error': f"CSV read error: {e}"
                }
        else:
            file_result = {
                'success': False,
                'filename': filename,
                'quotes_count': 0,
                'data': None,
                'error': f"Process failed: {result.stderr}"
            }
        
        # Clean up temp file
        if temp_output.exists():
            temp_output.unlink()
        
        # Update progress thread-safely
        with progress_lock:
            progress_data["completed"] += 1
            if file_result['success']:
                progress_data["results"].append(file_result)
            else:
                progress_data["errors"].append(file_result)
        
        return file_result
        
    except subprocess.TimeoutExpired:
        error_result = {
            'success': False,
            'filename': filename,
            'quotes_count': 0,
            'data': None,
            'error': "Process timed out (5 minutes)"
        }
        with progress_lock:
            progress_data["completed"] += 1
            progress_data["errors"].append(error_result)
        return error_result
        
    except Exception as e:
        error_result = {
            'success': False,
            'filename': filename,
            'quotes_count': 0,
            'data': None,
            'error': f"Unexpected error: {e}"
        }
        with progress_lock:
            progress_data["completed"] += 1
            progress_data["errors"].append(error_result)
        return error_result

def process_files_with_progress_parallel():
    """Process uploaded files with parallel processing and progress tracking"""
    if not st.session_state.uploaded_paths:
        st.error("No files uploaded")
        return
    
    # Reset progress data
    global progress_data
    with progress_lock:
        progress_data = {
            "completed": 0, 
            "total": len(st.session_state.uploaded_paths), 
            "results": [], 
            "errors": []
        }
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Determine number of workers (conservative approach)
    max_workers = min(3, len(st.session_state.uploaded_paths))  # Max 3 concurrent processes
    
    # Prepare file info for processing
    file_infos = [(i, path) for i, path in enumerate(st.session_state.uploaded_paths)]
    
    # Process files in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {executor.submit(process_single_file, file_info): file_info for file_info in file_infos}
        
        # Monitor progress
        while not all(future.done() for future in future_to_file):
            with progress_lock:
                completed = progress_data["completed"]
                total = progress_data["total"]
                progress = completed / total if total > 0 else 0
            
            progress_bar.progress(progress)
            status_text.text(f"Processing files... {completed}/{total} completed")
            
            # Update every 0.5 seconds
            import time
            time.sleep(0.5)
    
    # Final progress update
    progress_bar.progress(1.0)
    status_text.text("Processing complete!")
    
    # Collect results
    successful_results = []
    error_count = 0
    
    with progress_lock:
        for result in progress_data["results"]:
            if result['success'] and result['data'] is not None:
                successful_results.append(result['data'])
                st.success(f"✅ {result['filename']}: {result['quotes_count']} quotes extracted")
        
        for error in progress_data["errors"]:
            st.warning(f"⚠️ {error['filename']}: {error['error']}")
            error_count += 1
    
    # Combine successful results
    if successful_results:
        combined_df = pd.concat(successful_results, ignore_index=True)
        combined_df.to_csv(STAGE1_CSV, index=False)
        st.success(f"🎉 Processed {len(successful_results)} files successfully with {len(combined_df)} total quotes")
        if error_count > 0:
            st.warning(f"⚠️ {error_count} files had errors")
        st.session_state.current_step = 2
    else:
        st.error("No quotes extracted from any files")

def process_files_with_progress():
    """Legacy sequential processing - kept for fallback"""
    if not st.session_state.uploaded_paths:
        st.error("No files uploaded")
        return
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_files = len(st.session_state.uploaded_paths)
    all_results = []
    
    for i, path in enumerate(st.session_state.uploaded_paths):
        status_text.text(f"Processing {os.path.basename(path)}...")
        
        interviewee, company = extract_interviewee_and_company(os.path.basename(path))
        temp_output = BASE / f"temp_output_{i}.csv"
        
        result = subprocess.run([
            sys.executable, "-m", "voc_pipeline.modular_cli", "extract-core",
            path, company, interviewee, "closed_won", "2024-01-01", "-o", str(temp_output)
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and temp_output.exists():
            try:
                df_temp = pd.read_csv(temp_output)
                all_results.append(df_temp)
                st.success(f"✅ {os.path.basename(path)}: {len(df_temp)} quotes extracted")
            except Exception as e:
                st.warning(f"⚠️ {os.path.basename(path)}: {e}")
        
        if temp_output.exists():
            temp_output.unlink()
        
        progress_bar.progress((i + 1) / total_files)
    
    if all_results:
        combined_df = pd.concat(all_results, ignore_index=True)
        combined_df.to_csv(STAGE1_CSV, index=False)
        st.success(f"🎉 Processed {len(all_results)} files with {len(combined_df)} total quotes")
        st.session_state.current_step = 2
    else:
        st.error("No quotes extracted")

def save_stage1_to_supabase(csv_path):
    """Save Stage 1 results to Supabase"""
    if not SUPABASE_AVAILABLE:
        st.error("❌ Database not available")
        return False
    
    try:
        df = pd.read_csv(csv_path)
        saved_count = 0
        client_id = get_client_id()
        
        for _, row in df.iterrows():
            response_data = {
                'response_id': row.get('response_id', '') or row.get('Response ID', ''),
                'verbatim_response': row.get('verbatim_response', '') or row.get('Verbatim Response', ''),
                'subject': row.get('subject', '') or row.get('Subject', ''),
                'question': row.get('question', '') or row.get('Question', ''),
                'deal_status': row.get('deal_status', '') or row.get('Deal Status', 'closed_won'),
                'company': row.get('company', '') or row.get('Company Name', ''),
                'interviewee_name': row.get('interviewee_name', '') or row.get('Interviewee Name', ''),
                'interview_date': row.get('interview_date', '') or row.get('Date of Interview', '2024-01-01'),
                'file_source': 'stage1_processing',
                'client_id': client_id
            }
            if not response_data['response_id']:
                st.warning(f"Blank response_id for row: {row}")
            if db.save_core_response(response_data):
                saved_count += 1
        st.success(f"✅ Saved {saved_count} quotes to database for client: {client_id}")
        return True
    except Exception as e:
        st.error(f"❌ Failed to save to database: {e}")
        return False

def show_stage1_data_responses():
    """Stage 1: Data Response Table - Upload and extract quotes from interview files"""
    st.title("📊 Stage 1: Data Response Table")
    st.markdown("Upload interview transcripts and extract customer quotes and insights.")
    
    # File upload section
    st.subheader("📤 Upload Interview Files")
    uploaded_files = st.file_uploader(
        "Choose files",
        type=['txt', 'docx'],
        accept_multiple_files=True,
        help="Select one or more interview transcript files"
    )
    
    if uploaded_files:
        st.session_state.uploaded_paths = save_uploaded_files(uploaded_files)
        st.success(f"✅ Uploaded {len(uploaded_files)} files")
        
        # Show uploaded files
        st.subheader("📁 Uploaded Files")
        for i, path in enumerate(st.session_state.uploaded_paths):
            st.write(f"{i+1}. {os.path.basename(path)}")
        
        # Process button
        if st.button("🚀 Extract Quotes", type="primary", help="Process files to extract customer quotes"):
            with st.spinner("Extracting quotes from interviews..."):
                # Add processing mode selection
                processing_mode = st.radio(
                    "Processing Mode",
                    ["Parallel (Faster)", "Sequential (More Stable)"],
                    horizontal=True,
                    help="Parallel processing is faster but may use more resources"
                )
                
                if processing_mode == "Parallel (Faster)":
                    process_files_with_progress_parallel()
                else:
                    process_files_with_progress()
                    
                if SUPABASE_AVAILABLE and os.path.exists(STAGE1_CSV):
                    if save_stage1_to_supabase(STAGE1_CSV):
                        st.success("✅ Quotes extracted and saved to database")
                        st.session_state.current_step = 1
                        st.rerun()
                    else:
                        st.error("❌ Failed to save to database")
    
    # Show existing results
    if os.path.exists(STAGE1_CSV):
        st.subheader("📋 Extracted Quotes")
        df = pd.read_csv(STAGE1_CSV)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Quotes", len(df))
            with col2:
                if 'Subject' in df.columns:
                    st.metric("Topics Covered", df['Subject'].nunique())
                else:
                    st.metric("Topics Covered", "N/A")
            with col3:
                if 'Company Name' in df.columns:
                    st.metric("Companies", df['Company Name'].nunique())
                else:
                    st.metric("Companies", "N/A")
            
            # Export option
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Quotes",
                data=csv,
                file_name="extracted_quotes.csv",
                mime="text/csv",
                key="download_extracted_quotes"
            )
            
            # Proceed to Stage 2
            if st.button("🎯 Proceed to Stage 2: Label Quotes", type="primary"):
                st.session_state.current_step = 2
                st.rerun()
        else:
            st.info("📤 Please upload and process files first")
    
    # Processing details
    st.subheader("🔧 Processing Details")
    st.markdown("""
    **How the pipeline extracts quotes from your interviews (16K-optimized version):**
    
    **Batching & Parallel Processing:**
    - Multiple interviews are processed in parallel using Python's `ThreadPoolExecutor`
    - Each file is handled as a separate job for speed and efficiency
    
    **Advanced Chunking & Segmentation:**
    - Uses token-based chunking with ~2K tokens per chunk
    - Q&A-aware segmentation that preserves conversation boundaries
    - Intelligent overlap of 200 tokens to maintain continuity
    
    **Enhanced LLM Processing:**
    - Each chunk is sent to GPT-3.5-turbo-16k with comprehensive context
    - Extracts 3-5 quotes per chunk with detailed verbatim responses
    - Focuses on detailed customer experiences and specific examples
    """) 